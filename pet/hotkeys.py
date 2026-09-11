# -*- coding: utf-8 -*-
"""快捷键管理：应用内快捷键。"""
from __future__ import annotations

from typing import Callable, Dict
from PySide6.QtGui import QKeySequence, QShortcut


class HotkeyManager:
    """管理应用内全局快捷键。"""

    def __init__(self, parent):
        self._parent = parent
        self._shortcuts: Dict[str, QShortcut] = {}

    def register(self, name: str, key: str, callback: Callable) -> None:
        """注册快捷键。key 为 Qt 快捷键字符串，如 'Ctrl+Shift+C'。"""
        if name in self._shortcuts:
            self._shortcuts[name].setEnabled(False)
        sc = QShortcut(QKeySequence(key), self._parent)
        sc.activated.connect(callback)
        self._shortcuts[name] = sc

    def unregister(self, name: str) -> None:
        sc = self._shortcuts.pop(name, None)
        if sc:
            sc.setEnabled(False)
