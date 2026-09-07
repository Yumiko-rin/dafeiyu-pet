# -*- coding: utf-8 -*-
"""桌宠配置：类型化 + schema 校验 + 原子化保存。

使用独立的 pet_config.json，避免与系统监控台的 config.json 冲突。
修复原始项目 config 无校验、字段类型可能漂移的缺陷。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

SIZES = {"小": 0.55, "中": 0.7, "大": 0.9}
SPRITE_BASE_H = 340  # 精灵基准高度（px）

# 字段 schema（模块级，避免 dataclass 可变默认值陷阱）
SCHEMA: Dict[str, Any] = {
    "mode": ("enum", ("wander", "follow", "still")),
    "size": ("enum", tuple(SIZES.values())),
    "topmost": ("bool",),
    "passthrough": ("bool",),
    "autostart": ("bool",),
    "sound": ("bool",),
    "api_key": ("str",),
    "api_base": ("str",),
    "model": ("str",),
    "x": ("int_or_none",),
    "y": ("int_or_none",),
}

# 默认接入 DeepSeek 的 OpenAI 兼容 /v1 端点（保留开箱即用）
DEFAULT_API_BASE = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"


def app_dir() -> str:
    """桌宠数据目录（pet_config.json 等可写文件所在）：
    冻结时在可执行文件旁，否则在项目根目录。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_dir() -> str:
    """只读资源目录（sprites 等随包分发资源所在）：
    PyInstaller 单文件模式资源解压在 sys._MEIPASS，退回 exe 旁（兼容 onedir）；
    源码运行时为项目根目录。"""
    if getattr(sys, "frozen", False):
        for base in (getattr(sys, "_MEIPASS", None), os.path.dirname(sys.executable)):
            if base and os.path.isdir(os.path.join(base, "sprites")):
                return base
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sprite_dir() -> str:
    return os.path.join(resource_dir(), "sprites")


def sound_dir() -> str:
    """音效资源目录（sounds/ 与 sprites/ 同为随包分发资源）。"""
    return os.path.join(resource_dir(), "sounds")


def sprite_height(mult: float) -> int:
    """按倍率计算精灵高度。

    使用 round 而非 int：340*0.7 在浮点下为 237.999…，int 会截断成 237，
    导致预生成的 238/306 精灵文件永远命中不到。round 后精确得到 187/238/306。
    """
    return round(SPRITE_BASE_H * mult)


@dataclass
class PetConfig:
    """桌宠运行时配置。"""

    mode: str = "wander"            # wander | follow | still
    size: float = 0.7              # 0.55 | 0.7 | 0.9
    topmost: bool = True
    passthrough: bool = False
    autostart: bool = False
    sound: bool = True             # 音效开关（点击/收到回复轻响）
    api_key: str = ""              # 任意 OpenAI 兼容 /v1 端点的 API Key
    api_base: str = DEFAULT_API_BASE   # /v1 基址，chat 走 {api_base}/chat/completions
    model: str = DEFAULT_MODEL     # 模型名：deepseek-chat / gpt-4o / 本地模型名…
    x: Optional[int] = None
    y: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PetConfig":
        cfg = cls()
        if not isinstance(data, dict):
            return cfg
        for key, spec in SCHEMA.items():
            kind = spec[0]
            raw = data.get(key)
            value = getattr(cfg, key)
            if kind == "enum":
                if raw in spec[1]:
                    value = raw
            elif kind == "bool":
                if isinstance(raw, bool):
                    value = raw
            elif kind == "str":
                if isinstance(raw, str):
                    value = raw
            elif kind == "int_or_none":
                if raw is None or (isinstance(raw, int) and not isinstance(raw, bool)):
                    value = raw
            setattr(cfg, key, value)
        # 兼容旧配置：早期字段名为 ds_api_key
        if not cfg.api_key and isinstance(data.get("ds_api_key"), str):
            cfg.api_key = data["ds_api_key"]
        if not cfg.api_base:
            cfg.api_base = DEFAULT_API_BASE
        if not cfg.model:
            cfg.model = DEFAULT_MODEL
        return cfg

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def default_config_path() -> str:
    return os.path.join(app_dir(), "pet_config.json")


def load_config(path: str) -> PetConfig:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PetConfig.from_dict(data)
    except (OSError, ValueError, TypeError):
        return PetConfig()


def save_config(cfg: PetConfig, path: str) -> bool:
    try:
        directory = os.path.dirname(path) or "."
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(cfg.to_dict(), f, ensure_ascii=False, indent=2)
            os.replace(tmp, path)
            return True
        except Exception:
            if os.path.exists(tmp):
                os.remove(tmp)
            return False
    except OSError:
        return False
