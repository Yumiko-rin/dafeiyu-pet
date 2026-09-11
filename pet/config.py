# -*- coding: utf-8 -*-
"""桌宠配置：类型化 + schema 校验 + 原子化保存。

使用独立的 pet_config.json，避免与系统监控台的 config.json 冲突。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

SIZES = {"小": 0.55, "中": 0.7, "大": 0.9}
SPRITE_BASE_H = 340

SCHEMA: Dict[str, Any] = {
    "mode": ("enum", ("wander", "follow", "still")),
    "size": ("enum", tuple(SIZES.values())),
    "topmost": ("bool",),
    "passthrough": ("bool",),
    "autostart": ("bool",),
    "sound": ("bool",),
    "fx_enabled": ("bool",),
    "x": ("int_or_none",),
    "y": ("int_or_none",),
    "theme": ("str",),
}


def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_dir() -> str:
    if getattr(sys, "frozen", False):
        for base in (getattr(sys, "_MEIPASS", None), os.path.dirname(sys.executable)):
            if base and os.path.isdir(os.path.join(base, "sprites")):
                return base
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sprite_dir() -> str:
    return os.path.join(resource_dir(), "sprites")


def sound_dir() -> str:
    return os.path.join(resource_dir(), "sounds")


def sprite_height(mult: float) -> int:
    return round(SPRITE_BASE_H * mult)


@dataclass
class PetConfig:
    mode: str = "wander"
    size: float = 0.7
    topmost: bool = True
    passthrough: bool = False
    autostart: bool = False
    sound: bool = True
    fx_enabled: bool = True
    theme: str = "默认紫"
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
