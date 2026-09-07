# -*- coding: utf-8 -*-
"""桌宠后台服务：兼容任意 OpenAI /v1 端点的 AI 对话 + DeepSeek 余额查询。

网络请求均在后台线程执行，结果经「线程安全队列」回传，主线程轮询消费，
避免阻塞桌宠动画主线程；聊天历史带锁保护，避免多线程数据竞争。

新增：
- requests.Session 复用（减少握手开销，更稳定）；
- 端点 / 模型 / Key 全部可配置，默认接入 DeepSeek 的 /v1（开箱即用）；
- 聊天历史持久化到 app_dir/chat_history.jsonl，重启后自动回放。
"""
from __future__ import annotations

import json
import os
import queue
import threading
from typing import List, Tuple

import requests

from .config import app_dir, DEFAULT_API_BASE, DEFAULT_MODEL

# 鲸鱼娘人设提示词（与具体模型 / 服务无关）
DS_SYSTEM = (
    "你是桌宠鲸鱼娘「大肥鱼」：聪明但懒、傲娇嘴甜；主食白米饭，自称吃白饭的大肥鱼"
    "（但绝对拒绝被叫胖）；管用户叫「主人」或「鱼片」。"
    "回复口语化、轻松有梗，80 字以内，可适当用 🐳🍚 表情；"
    "不聊政治与敏感话题，不提自己的模型实现细节。"
)

# DeepSeek 账户余额查询接口（仅 DeepSeek 可用；其它提供商用不到此功能）
_BALANCE_URL = "https://api.deepseek.com/user/balance"

# 持久化文件名（位于 app_dir，随 exe 旁）
_HISTORY_FILE = "chat_history.jsonl"


class PetServices:
    """后台服务：AI 对话 + 余额查询。

    消息队列元素：
        ("say", text)            -> 主窗口气泡
        ("chat", role, text)     -> 对话面板；role ∈ user/assistant/err
    """

    def __init__(
        self,
        api_key: str = "",
        api_base: str = DEFAULT_API_BASE,
        model: str = DEFAULT_MODEL,
    ):
        self.api_key = api_key
        self.api_base = (api_base or DEFAULT_API_BASE).rstrip("/")
        self.model = model or DEFAULT_MODEL
        self._messages: "queue.Queue[Tuple]" = queue.Queue()
        self._history: List[dict] = []
        self._history_lock = threading.Lock()
        self._busy = False
        self._max_history = 40
        # 复用 Session，减少 TLS 握手、提升稳定性
        self._session = requests.Session()
        # 启动时从磁盘载入历史，保证重启后对话可回放
        self._hist_file = os.path.join(app_dir(), _HISTORY_FILE)
        self._load_history()

    # ---------- 端点 ----------
    def _chat_url(self) -> str:
        return f"{self.api_base}/chat/completions"

    def configure(self, api_key: str = "", api_base: str = "", model: str = "") -> None:
        """运行期更新端点配置（设置面板保存时调用）。"""
        if api_key is not None:
            self.api_key = api_key
        if api_base:
            self.api_base = api_base.rstrip("/")
        if model:
            self.model = model

    # ---------- 历史持久化 ----------
    def _load_history(self) -> None:
        """从 JSONL 载入历史（每行一个 {role,content}）。"""
        try:
            with open(self._hist_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if (
                        isinstance(d, dict)
                        and d.get("role") in ("user", "assistant", "err")
                        and "content" in d
                    ):
                        self._history.append(
                            {"role": d["role"], "content": d["content"]}
                        )
        except (OSError, ValueError):
            pass
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def _persist_history(self) -> None:
        """原子写入当前历史（仅保留最近 _max_history 条）。"""
        try:
            tmp = self._hist_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                for d in self._history[-self._max_history:]:
                    f.write(
                        json.dumps(
                            {"role": d["role"], "content": d["content"]},
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            os.replace(tmp, self._hist_file)
        except OSError:
            pass

    def get_history(self) -> List[dict]:
        """回放历史给对话面板首屏使用（返回副本）。"""
        with self._history_lock:
            return [dict(d) for d in self._history[-self._max_history:]]

    # ---------- 状态 ----------
    def is_busy(self) -> bool:
        return self._busy

    # ---------- AI 对话 ----------
    def ask(self, user_msg: str) -> bool:
        """发起一轮对话；未配置 Key 或上一轮未结束返回 False。"""
        if self._busy or not self.api_key:
            return False
        self._busy = True
        threading.Thread(target=self._ask_worker, args=(user_msg,), daemon=True).start()
        return True

    def _ask_worker(self, user_msg: str) -> None:
        try:
            with self._history_lock:
                history = list(self._history[-self._max_history:])
            messages = [{"role": "system", "content": DS_SYSTEM}]
            messages.extend(history)
            messages.append({"role": "user", "content": user_msg})

            resp = self._session.post(
                self._chat_url(),
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": 300,
                    "temperature": 0.85,
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=(10, 90),
            )

            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"].strip()
                with self._history_lock:
                    self._history.append({"role": "user", "content": user_msg})
                    self._history.append({"role": "assistant", "content": reply})
                    if len(self._history) > self._max_history:
                        self._history = self._history[-self._max_history:]
                # 落盘持久化（带锁外写入，避免阻塞）
                self._persist_history()
                self._messages.put(("chat", "assistant", reply))
            else:
                err = resp.json().get("error", {}).get("message", str(resp.status_code))
                self._messages.put(("chat", "err", f"深海断线：{err[:40]}"))
        except requests.exceptions.Timeout:
            self._messages.put(("chat", "err", "深海断线：请求超时，检查网络"))
        except requests.exceptions.ConnectionError:
            self._messages.put(("chat", "err", "深海断线：连不上，检查网络"))
        except Exception as ex:  # noqa: BLE001
            self._messages.put(("chat", "err", f"深海断线：{str(ex)[:40]}"))
        finally:
            self._busy = False

    # ---------- 模型余额（仅 DeepSeek） ----------
    def fetch_balance(self) -> None:
        """后台线程查询 DeepSeek 账户余额（经主气泡播报）。"""
        threading.Thread(target=self._balance_worker, daemon=True).start()

    def _balance_worker(self) -> None:
        if not self.api_key:
            self._messages.put(("say", "请先设置 API Key！"))
            return
        try:
            r = self._session.get(
                _BALANCE_URL,
                timeout=10,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if r.status_code == 200:
                data = r.json()
                infos = data.get("balance_infos") or []
                if data.get("is_available") and infos:
                    balance = infos[0].get("total_balance", "0.00")
                    currency = infos[0].get("currency", "CNY")
                    symbol = "¥" if currency == "CNY" else f"{currency} "
                    self._messages.put(("say", f"模型余额：{symbol}{balance}"))
                else:
                    self._messages.put(("say", "余额不足或未开通"))
            else:
                err = r.json().get("error", {}).get("message", str(r.status_code))
                self._messages.put(("say", f"查询失败: {err[:12]}"))
        except requests.exceptions.Timeout:
            self._messages.put(("say", "余额查询超时"))
        except requests.exceptions.ConnectionError:
            self._messages.put(("say", "余额查询连接失败"))
        except Exception as ex:  # noqa: BLE001
            self._messages.put(("say", f"余额查询失败: {str(ex)[:12]}"))

    # ---------- 消息消费 ----------
    def drain_messages(self) -> List[Tuple]:
        """主线程轮询：一次性取出所有待处理消息。"""
        out: List[Tuple] = []
        while True:
            try:
                out.append(self._messages.get_nowait())
            except queue.Empty:
                break
        return out
