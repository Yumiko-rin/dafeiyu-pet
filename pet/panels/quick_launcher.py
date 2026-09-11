# -*- coding: utf-8 -*-
"""快捷启动器面板：快速启动常用应用/网站。"""
from __future__ import annotations

import json
import os
import subprocess
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from ..config import app_dir
from ..styles import (
    CJK_FONT, INPUT_CSS, HINT_CSS, LIST_CSS, BTN_CSS, atomic_json_write,
)
from .base import BasePanel

LAUNCH_BTN_CSS = BTN_CSS + (
    "QPushButton#delBtn { background: rgba(255,90,110,0.7); }"
    "QPushButton#delBtn:hover { background: rgba(255,90,110,1.0); }"
)

_LAUNCHER_FILE = "quick_launcher.json"

DEFAULT_SHORTCUTS = [
    {"name": "记事本", "path": "notepad.exe"},
    {"name": "计算器", "path": "calc.exe"},
    {"name": "文件管理器", "path": "explorer.exe"},
    {"name": "浏览器", "path": "https://www.bing.com"},
]


class QuickLauncherPanel(BasePanel):
    """快捷启动器面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, title="快捷启动器", width=300, height=360)
        self._data_path = os.path.join(app_dir(), _LAUNCHER_FILE)
        self._shortcuts = []
        self._load()

    def _build_content(self, lay: QVBoxLayout) -> None:
        lay.setSpacing(8)

        self.shortcut_list = QListWidget()
        self.shortcut_list.setStyleSheet(LIST_CSS)
        self.shortcut_list.itemDoubleClicked.connect(self._launch)
        lay.addWidget(self.shortcut_list, 1)

        add_row = QHBoxLayout()
        add_row.setSpacing(6)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("名称")
        self.name_edit.setStyleSheet(INPUT_CSS)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("路径或网址 (如 notepad / https://...)")
        self.path_edit.setStyleSheet(INPUT_CSS)
        add_row.addWidget(self.name_edit, 1)
        add_row.addWidget(self.path_edit, 2)
        lay.addLayout(add_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        add_btn = QPushButton("添加")
        add_btn.setStyleSheet(LAUNCH_BTN_CSS)
        add_btn.clicked.connect(self._add_shortcut)
        del_btn = QPushButton("删除选中")
        del_btn.setObjectName("delBtn")
        del_btn.setStyleSheet(LAUNCH_BTN_CSS)
        del_btn.clicked.connect(self._del_shortcut)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        lay.addLayout(btn_row)

        hint = QLabel("双击条目启动 · 支持 exe / 文件夹 / 网址")
        hint.setStyleSheet(HINT_CSS)
        lay.addWidget(hint)

    def _load(self) -> None:
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                self._shortcuts = json.load(f)
            if not isinstance(self._shortcuts, list):
                self._shortcuts = list(DEFAULT_SHORTCUTS)
        except (OSError, ValueError):
            self._shortcuts = [dict(s) for s in DEFAULT_SHORTCUTS]
        self._refresh()

    def _persist(self) -> None:
        atomic_json_write(self._data_path, self._shortcuts, indent=2)

    def _refresh(self) -> None:
        self.shortcut_list.clear()
        for s in self._shortcuts:
            self.shortcut_list.addItem(f"{s['name']}  →  {s['path']}")

    def _add_shortcut(self) -> None:
        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()
        if not name or not path:
            return
        self._shortcuts.append({"name": name, "path": path})
        self.name_edit.clear()
        self.path_edit.clear()
        self._refresh()
        self._persist()

    def _del_shortcut(self) -> None:
        row = self.shortcut_list.currentRow()
        if 0 <= row < len(self._shortcuts):
            self._shortcuts.pop(row)
            self._refresh()
            self._persist()

    def _launch(self, item: QListWidgetItem) -> None:
        row = self.shortcut_list.row(item)
        if 0 <= row < len(self._shortcuts):
            path = self._shortcuts[row]["path"]
            try:
                if path.startswith("http://") or path.startswith("https://"):
                    webbrowser.open(path)
                elif os.path.isfile(path) or os.path.isdir(path):
                    os.startfile(path)
                else:
                    subprocess.Popen([path], shell=False)
            except Exception:
                pass
