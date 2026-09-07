# -*- coding: utf-8 -*-
"""音效管理：点击/收到回复的轻响。

- 资源为项目内自带的 WAV（sounds/pop.wav、sounds/ding.wav），
  由 tools/gen_sounds.py 合成，无外部依赖；
- 使用 PySide6.QtMultimedia.QSoundEffect 播放（纯 WAV、带缓存、异步）；
- 资源缺失或播放失败一律静默跳过，绝不影响桌宠主流程；
- enabled 开关与配置项 sound 联动，可在设置面板关闭。
"""
from __future__ import annotations

import os

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from .config import sound_dir


class SoundManager:
    """极简音效播放器。"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._effects: dict = {}

    def _path(self, name: str) -> str:
        return os.path.join(sound_dir(), f"{name}.wav")

    def _effect(self, name: str):
        """获取（并缓存）一个已设置好音源的 QSoundEffect；缺失返回 None。"""
        if name not in self._effects:
            p = self._path(name)
            if not os.path.exists(p):
                self._effects[name] = None
                return None
            try:
                fx = QSoundEffect()
                fx.setSource(QUrl.fromLocalFile(p))
                fx.setVolume(0.6)
                self._effects[name] = fx
            except Exception:  # noqa: BLE001
                self._effects[name] = None
        return self._effects[name]

    def play(self, name: str) -> None:
        """播放 sounds/ 下的 WAV；关闭 / 缺失 / 异常均静默返回。"""
        if not self.enabled:
            return
        try:
            fx = self._effect(name)
            if fx is not None:
                fx.play()
        except Exception:  # noqa: BLE001
            pass
