# -*- coding: utf-8 -*-
"""便签/备忘录面板：桌面便签，自动保存。"""
from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout,
    QToolButton,
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
NOTE_CSS = (
    "QTextEdit { background: rgba(255,255,255,0.06); color: #f3f1ff;"
    "border: 1px solid rgba(148,130,255,0.2); border-radius: 10px;"
    "padding: 8px; font-size: 14px; font-family: " + CJK_FONT + ";"
    "selection-background-color: rgba(111,108,255,0.5); }"
)
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 8px; font-size: 12px; font-weight: bold; padding: 6px 12px;"
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

_NOTES_FILE = "sticky_notes.json"


class StickyNotesPanel(QDialog):
    """便签/备忘录面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("便签备忘录")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, 300, 380)
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
        title = QLabel("便签备忘录")
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

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("在这里记录你的想法...")
        self.notes_edit.setStyleSheet(NOTE_CSS)
        lay.addWidget(self.notes_edit, 1)

        hint = QLabel("自动保存 · 重启不丢失")
        hint.setStyleSheet(HINT_CSS)
        lay.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet(BTN_CSS)
        save_btn.clicked.connect(self._save)
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("delBtn")
        clear_btn.setStyleSheet(BTN_CSS)
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(clear_btn)
        lay.addLayout(btn_row)

        self._notes_path = os.path.join(app_dir(), _NOTES_FILE)
        self._load()
        self.hide()

    def _load(self) -> None:
        try:
            with open(self._notes_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "text" in data:
                self.notes_edit.setPlainText(data["text"])
        except (OSError, ValueError):
            pass

    def _save(self) -> None:
        try:
            with open(self._notes_path, "w", encoding="utf-8") as f:
                json.dump({"text": self.notes_edit.toPlainText()}, f, ensure_ascii=False)
        except OSError:
            pass

    def _clear(self) -> None:
        self.notes_edit.clear()
        self._save()

    def closeEvent(self, event) -> None:
        self._save()
        super().closeEvent(event)

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
