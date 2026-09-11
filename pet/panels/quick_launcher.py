# -*- coding: utf-8 -*-
"""快捷启动器面板：快速启动常用应用/网站。"""
from __future__ import annotations

import json
import os
import subprocess
import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout, QToolButton,
)

from ..config import app_dir

CJK_FONT = (
    '"Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC",'
    ' "Source Han Sans SC", "Noto Sans CJK SC", sans-serif'
)
CARD_CSS = (
    "QFrame#card { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 rgba(38,36,66,0.98), stop:1 rgba(24,22,48,0.98));"
    "border: 1px solid rgba(148,130,255,0.35); border-radius: 16px;"
    "font-family: " + CJK_FONT + "; }"
)
TITLE_CSS = "QLabel { color: #f4f2ff; font-size: 15px; font-weight: 600; font-family: " + CJK_FONT + "; }"
LIST_CSS = (
    "QListWidget { background: rgba(255,255,255,0.05); color: #e0dcf8;"
    "border: 1px solid rgba(148,130,255,0.15); border-radius: 8px;"
    "padding: 4px; font-size: 13px; font-family: " + CJK_FONT + "; }"
    "QListWidget::item { padding: 6px 8px; border-radius: 6px; }"
    "QListWidget::item:selected { background: rgba(111,108,255,0.4); }"
    "QListWidget::item:hover { background: rgba(148,130,255,0.2); }"
)
INPUT_CSS = (
    "QLineEdit { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "padding: 6px 10px; font-size: 13px; font-family: " + CJK_FONT + "; }"
    "QLineEdit:focus { border: 1px solid rgba(140,128,255,0.8); }"
)
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 8px; font-size: 12px; font-weight: bold; padding: 6px 10px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
    "QPushButton#delBtn { background: rgba(255,90,110,0.7); }"
    "QPushButton#delBtn:hover { background: rgba(255,90,110,1.0); }"
)
HINT_CSS = "QLabel { color: #9a94cf; font-size: 11px; font-family: " + CJK_FONT + "; }"
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
)

_LAUNCHER_FILE = "quick_launcher.json"

DEFAULT_SHORTCUTS = [
    {"name": "记事本", "path": "notepad.exe"},
    {"name": "计算器", "path": "calc.exe"},
    {"name": "文件管理器", "path": "explorer.exe"},
    {"name": "浏览器", "path": "https://www.bing.com"},
]


class QuickLauncherPanel(QDialog):
    """快捷启动器面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("快捷启动器")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, 300, 360)
        card.setStyleSheet(CARD_CSS)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(10, 6, 60, 160))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(0)
        title = QLabel("快捷启动器")
        title.setStyleSheet(TITLE_CSS)
        head.addWidget(title)
        head.addStretch(1)
        close_btn = QToolButton()
        close_btn.setText("\u2715")
        close_btn.setFixedSize(26, 26)
        close_btn.setStyleSheet(CLOSE_CSS)
        close_btn.clicked.connect(self.hide)
        head.addWidget(close_btn)
        lay.addLayout(head)

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
        add_btn.setStyleSheet(BTN_CSS)
        add_btn.clicked.connect(self._add_shortcut)
        del_btn = QPushButton("删除选中")
        del_btn.setObjectName("delBtn")
        del_btn.setStyleSheet(BTN_CSS)
        del_btn.clicked.connect(self._del_shortcut)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(del_btn)
        lay.addLayout(btn_row)

        hint = QLabel("双击条目启动 · 支持 exe / 文件夹 / 网址")
        hint.setStyleSheet(HINT_CSS)
        lay.addWidget(hint)

        self._data_path = os.path.join(app_dir(), _LAUNCHER_FILE)
        self._shortcuts = []
        self._load()
        self.hide()

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
        try:
            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump(self._shortcuts, f, ensure_ascii=False, indent=2)
        except OSError:
            pass

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
                elif os.path.isfile(path):
                    os.startfile(path)
                elif os.path.isdir(path):
                    os.startfile(path)
                else:
                    subprocess.Popen([path])
            except Exception:
                pass

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
