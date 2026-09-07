# -*- coding: utf-8 -*-
"""可视化设置面板：把分散在右键菜单里的开关集中到一个对话框。

覆盖：API 网址（/v1 基址）/ API Key / 模型（可一键拉取列表）/ 运动模式 / 大小 /
置顶 / 鼠标穿透 / 开机自启 / 音效。
保存时统一回调 on_apply(new_cfg)，由 PetWindow 负责按字段落地生效。
"""
from __future__ import annotations

import json
import os
import socket
import threading

import requests
from typing import Callable, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import PetConfig, SIZES, DEFAULT_API_BASE, DEFAULT_MODEL, app_dir

# 模型列表本地缓存文件（app_dir/known_models.json：{api_base: [model_ids]}）
# 拉取成功一次即缓存，下次开面板秒级预填，网络慢/挂也不影响选模型
_KNOWN_MODELS_FILE = "known_models.json"

CJK_FONT = (
    '"Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC",'
    ' "Source Han Sans SC", "Noto Sans CJK SC", sans-serif'
)
CARD_CSS = (
    "QWidget#setCard { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 rgba(38,36,66,0.98), stop:1 rgba(24,22,48,0.98));"
    "border: 1px solid rgba(148,130,255,0.35); border-radius: 16px;"
    "font-family: " + CJK_FONT + "; }"
)
TITLE_CSS = (
    "QLabel { color: #f4f2ff; font-size: 15px; font-weight: 600;"
    "font-family: " + CJK_FONT + "; }"
)
LABEL_CSS = (
    "QLabel { color: #cfc9f2; font-size: 13px; font-family: " + CJK_FONT + "; }"
)
HINT_CSS = (
    "QLabel { color: #9a94cf; font-size: 11px; font-family: " + CJK_FONT + "; }"
)
INPUT_CSS = (
    "QLineEdit { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "padding: 6px 10px; font-size: 13px; font-family: " + CJK_FONT + "; }"
    "QLineEdit:focus { border: 1px solid rgba(140,128,255,0.8); }"
)
COMBO_CSS = (
    "QComboBox { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "padding: 5px 8px; font-size: 13px; font-family: " + CJK_FONT + "; }"
    "QComboBox QAbstractItemView { background: #2a2848; color: #f3f1ff;"
    "selection-background-color: #6f6cff; font-family: " + CJK_FONT + "; }"
)
CHECK_CSS = (
    "QCheckBox { color: #cfc9f2; font-size: 13px; spacing: 6px;"
    "font-family: " + CJK_FONT + "; }"
    "QCheckBox::indicator { width: 16px; height: 16px;"
    "border-radius: 4px; border: 1px solid rgba(148,130,255,0.6);"
    "background: rgba(255,255,255,0.08); }"
    "QCheckBox::indicator:checked { background: #6f6cff;"
    "image: none; border: 1px solid #8f8cff; }"
)
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 14px; font-weight: bold; padding: 8px 0;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
    "QPushButton:disabled { background: rgba(120,120,160,0.5); }"
    "QPushButton#ghost { background: rgba(255,255,255,0.10); color: #cfc9f2;"
    "border: 1px solid rgba(255,255,255,0.18); font-weight: 500; padding: 6px 10px; }"
)

MODE_ITEMS = (("自由散步", "wander"), ("跟随鼠标", "follow"), ("原地待着", "still"))
SIZE_ITEMS = tuple(SIZES.items())  # (("小",0.55), ("中",0.7), ("大",0.9))
# 常见模型预填，拉取失败也能直接选
COMMON_MODELS = [
    "deepseek-chat",
    "deepseek-reasoner",
    "gpt-4o",
    "gpt-4o-mini",
    "glm-4-plus",
    "qwen-max",
]


class SettingsDialog(QDialog):
    """大肥鱼设置面板。"""

    # 模型列表拉取完成信号：后台线程 emit -> 主线程槽（跨线程安全，
    # 不用 QTimer.singleShot —— Python 线程没有 Qt 事件循环，回调永不触发）
    _models_ready = Signal(list, str, str)

    def __init__(self, cfg: PetConfig, on_apply: Callable[[PetConfig], None], parent=None):
        super().__init__(parent, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("大肥鱼 · 设置")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self._on_apply = on_apply
        self._models_ready.connect(self._on_models)
        self._build(cfg)
        self.setFixedSize(400, 470)

    def _build(self, cfg: PetConfig) -> None:
        root = QWidget(self)
        root.setObjectName("setCard")
        root.setGeometry(0, 0, 400, 470)
        root.setStyleSheet(CARD_CSS)

        lay = QVBoxLayout(root)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        title = QLabel("大肥鱼 · 设置")
        title.setStyleSheet(TITLE_CSS)
        lay.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        # ---- API 网址（/v1 基址）----
        self.base_edit = QLineEdit(cfg.api_base or DEFAULT_API_BASE)
        self.base_edit.setPlaceholderText("https://api.deepseek.com/v1")
        self.base_edit.setStyleSheet(INPUT_CSS)
        base_lbl = QLabel("API 网址")
        base_lbl.setStyleSheet(LABEL_CSS)
        form.addRow(base_lbl, self.base_edit)

        # ---- API Key ----
        key_row = QWidget()
        key_h = QHBoxLayout(key_row)
        key_h.setContentsMargins(0, 0, 0, 0)
        key_h.setSpacing(8)
        self.key_edit = QLineEdit(cfg.api_key)
        self.key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_edit.setPlaceholderText("留空则无法使用鲸语讯道")
        self.key_edit.setStyleSheet(INPUT_CSS)
        self.show_key = QCheckBox("显示")
        self.show_key.setStyleSheet(CHECK_CSS)
        self.show_key.toggled.connect(
            lambda on: self.key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
            )
        )
        key_h.addWidget(self.key_edit, 1)
        key_h.addWidget(self.show_key)
        key_lbl = QLabel("API Key")
        key_lbl.setStyleSheet(LABEL_CSS)
        form.addRow(key_lbl, key_row)

        # ---- 模型（可编辑下拉 + 一键拉取）----
        model_row = QWidget()
        model_h = QHBoxLayout(model_row)
        model_h.setContentsMargins(0, 0, 0, 0)
        model_h.setSpacing(8)
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setStyleSheet(COMBO_CSS)
        presets = list(COMMON_MODELS)
        if cfg.model and cfg.model not in presets:
            presets.insert(0, cfg.model)
        self.model_combo.addItems(presets)
        if cfg.model:
            idx = self.model_combo.findText(cfg.model)
            self.model_combo.setCurrentIndex(idx if idx >= 0 else 0)
        model_h.addWidget(self.model_combo, 1)
        self.model_refresh = QPushButton("刷新列表")
        self.model_refresh.setObjectName("ghost")
        self.model_refresh.setStyleSheet(BTN_CSS)
        self.model_refresh.clicked.connect(self._fetch_models)
        model_h.addWidget(self.model_refresh)
        model_lbl = QLabel("模型")
        model_lbl.setStyleSheet(LABEL_CSS)
        form.addRow(model_lbl, model_row)

        self.model_status = QLabel("填好网址+Key 后点「刷新列表」自动获取")
        self.model_status.setStyleSheet(HINT_CSS)
        form.addRow("", self.model_status)

        # 本地缓存预填：上次成功拉取过的模型秒级呈现，不必等网络
        base_key = (cfg.api_base or DEFAULT_API_BASE).rstrip("/")
        cached = self._load_known_models().get(base_key) or []
        if cached:
            cur = cfg.model or self.model_combo.currentText().strip()
            self.model_combo.clear()
            self.model_combo.addItems(cached)
            if cur and cur not in cached:
                self.model_combo.setEditText(cur)
            self.model_status.setText(f"已载入上次获取的 {len(cached)} 个模型；点「刷新列表」可更新")

        # ---- 模式 ----
        self.mode_combo = QComboBox()
        self.mode_combo.setStyleSheet(COMBO_CSS)
        for label, key in MODE_ITEMS:
            self.mode_combo.addItem(label, key)
        idx = next((i for i, (_, k) in enumerate(MODE_ITEMS) if k == cfg.mode), 0)
        self.mode_combo.setCurrentIndex(idx)
        mode_lbl = QLabel("运动模式")
        mode_lbl.setStyleSheet(LABEL_CSS)
        form.addRow(mode_lbl, self.mode_combo)

        # ---- 大小 ----
        self.size_combo = QComboBox()
        self.size_combo.setStyleSheet(COMBO_CSS)
        for label, mult in SIZE_ITEMS:
            self.size_combo.addItem(label, mult)
        sidx = next((i for i, (_, v) in enumerate(SIZE_ITEMS) if abs(v - cfg.size) < 0.01), 1)
        self.size_combo.setCurrentIndex(sidx)
        size_lbl = QLabel("桌宠大小")
        size_lbl.setStyleSheet(LABEL_CSS)
        form.addRow(size_lbl, self.size_combo)

        # ---- 开关 ----
        self.topmost_chk = QCheckBox("窗口置顶（始终在前面）")
        self.topmost_chk.setChecked(cfg.topmost)
        self.topmost_chk.setStyleSheet(CHECK_CSS)
        self.pass_chk = QCheckBox("鼠标穿透（点不到它，只能戳菜单）")
        self.pass_chk.setChecked(cfg.passthrough)
        self.pass_chk.setStyleSheet(CHECK_CSS)
        self.auto_chk = QCheckBox("开机自启")
        self.auto_chk.setChecked(cfg.autostart)
        self.auto_chk.setStyleSheet(CHECK_CSS)
        self.sound_chk = QCheckBox("音效（点击 / 收到回复轻响）")
        self.sound_chk.setChecked(cfg.sound)
        self.sound_chk.setStyleSheet(CHECK_CSS)

        form.addRow(self.topmost_chk)
        form.addRow(self.pass_chk)
        form.addRow(self.auto_chk)
        form.addRow(self.sound_chk)

        lay.addLayout(form)
        lay.addStretch(1)

        # ---- 按钮 ----
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = QPushButton("取消")
        cancel.setObjectName("cancel")
        cancel.setStyleSheet(BTN_CSS)
        cancel.clicked.connect(self.reject)
        save = QPushButton("保存并应用")
        save.setStyleSheet(BTN_CSS)
        save.clicked.connect(self._on_save)
        btn_row.addWidget(cancel, 1)
        btn_row.addWidget(save, 1)
        lay.addLayout(btn_row)

    # ---------- 模型列表本地缓存 ----------
    def _load_known_models(self) -> dict:
        """读取 {api_base: [model_ids]} 缓存（损坏/缺失返回空）。"""
        try:
            with open(
                os.path.join(app_dir(), _KNOWN_MODELS_FILE), "r", encoding="utf-8"
            ) as f:
                d = json.load(f)
            return d if isinstance(d, dict) else {}
        except (OSError, ValueError):
            return {}

    def _save_known_models(self, base_key: str, ids: List[str]) -> None:
        """写入成功后缓存；保留其它端点的记录，每个端点只存最近一次。"""
        try:
            path = os.path.join(app_dir(), _KNOWN_MODELS_FILE)
            data = self._load_known_models()
            data[base_key] = ids
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except OSError:
            pass

    # ---------- 自动获取模型列表 ----------
    def _fetch_models(self) -> None:
        base = self.base_edit.text().strip() or DEFAULT_API_BASE
        key = self.key_edit.text().strip()
        if not key:
            self.model_status.setText("先填 API Key 再刷新～")
            return
        self.model_refresh.setEnabled(False)
        self.model_status.setText("正在获取模型列表…")
        cur_text = self.model_combo.currentText().strip()

        def work() -> None:
            try:
                # DNS 预检：解析失败立即报错，不白等
                host = base.split("//")[-1].split("/")[0].split(":")[0]
                try:
                    socket.gethostbyname(host)
                except socket.gaierror:
                    self._models_ready.emit([], f"域名解析失败：{host}", cur_text)
                    return
                url = base.rstrip("/") + "/models"
                r = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=(5, 30),  # 连接 5s 快失败；读取 30s 兼容慢端点（商汤偶发 10-20s）
                )
                if r.status_code == 200:
                    data = r.json()
                    ids: List[str] = [
                        m["id"]
                        for m in data.get("data", [])
                        if isinstance(m, dict) and m.get("id")
                    ]
                    self._models_ready.emit(ids, "", cur_text)
                else:
                    err = r.json().get("error", {}).get("message", str(r.status_code))
                    self._models_ready.emit([], f"HTTP {r.status_code}: {err[:30]}", cur_text)
            except requests.exceptions.SSLError:
                self._models_ready.emit([], "SSL 证书校验失败（检查网址是否 https）", cur_text)
            except requests.exceptions.ConnectTimeout:
                self._models_ready.emit([], "连接超时：网址不通或网络受限", cur_text)
            except requests.exceptions.ReadTimeout:
                self._models_ready.emit([], "读取超时：端点响应过慢", cur_text)
            except requests.exceptions.ConnectionError:
                self._models_ready.emit([], "连接失败：检查网址与网络", cur_text)
            except requests.exceptions.MissingSchema:
                self._models_ready.emit([], "网址格式不对：需以 http(s):// 开头", cur_text)
            except Exception as ex:  # noqa: BLE001
                self._models_ready.emit([], str(ex)[:50], cur_text)

        threading.Thread(target=work, daemon=True).start()

    def _on_models(self, ids: List[str], err: str, cur_text: str) -> None:
        self.model_refresh.setEnabled(True)
        if err:
            self.model_status.setText(f"获取失败：{err}")
            return
        if not ids:
            self.model_status.setText("该端点未返回模型（可能不支持 /models）")
            return
        base_key = (self.base_edit.text().strip() or DEFAULT_API_BASE).rstrip("/")
        self._save_known_models(base_key, ids)
        self.model_combo.clear()
        self.model_combo.addItems(ids)
        if cur_text and cur_text in ids:
            self.model_combo.setCurrentText(cur_text)
        elif cur_text:
            self.model_combo.setEditText(cur_text)
        self.model_status.setText(f"已获取 {len(ids)} 个模型，直接选或手动改")

    # ---------- 保存 ----------
    def _on_save(self) -> None:
        new = PetConfig(
            mode=self.mode_combo.currentData(),
            size=float(self.size_combo.currentData()),
            topmost=self.topmost_chk.isChecked(),
            passthrough=self.pass_chk.isChecked(),
            autostart=self.auto_chk.isChecked(),
            sound=self.sound_chk.isChecked(),
            api_key=self.key_edit.text().strip(),
            api_base=self.base_edit.text().strip() or DEFAULT_API_BASE,
            model=self.model_combo.currentText().strip() or DEFAULT_MODEL,
            x=None,
            y=None,
        )
        self._on_apply(new)
        self.accept()
