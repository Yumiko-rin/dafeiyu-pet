# -*- coding: utf-8 -*-
"""便签/备忘录面板：桌面便签，自动保存。"""
from __future__ import annotations

import json
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout

from ..config import app_dir
from ..styles import (
    CJK_FONT, HINT_CSS, BTN_CSS, atomic_json_write,
)
from .base import BasePanel

NOTE_CSS = (
    "QTextEdit { background: rgba(255,255,255,0.06); color: #f3f1ff;"
    "border: 1px solid rgba(148,130,255,0.2); border-radius: 10px;"
    "padding: 8px; font-size: 14px; font-family: " + CJK_FONT + ";"
    "selection-background-color: rgba(111,108,255,0.5); }"
)
STICKY_BTN_CSS = BTN_CSS + (
    "QPushButton#delBtn { background: rgba(255,90,110,0.7); }"
    "QPushButton#delBtn:hover { background: rgba(255,90,110,1.0); }"
)

_NOTES_FILE = "sticky_notes.json"


class StickyNotesPanel(BasePanel):
    """便签/备忘录面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, title="便签备忘录", width=300, height=380)
        self._notes_path = os.path.join(app_dir(), _NOTES_FILE)
        self._load()

    def _build_content(self, lay: QVBoxLayout) -> None:
        lay.setSpacing(8)

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
        save_btn.setStyleSheet(STICKY_BTN_CSS)
        save_btn.clicked.connect(self._save)
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("delBtn")
        clear_btn.setStyleSheet(STICKY_BTN_CSS)
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(save_btn)
        btn_row.addWidget(clear_btn)
        lay.addLayout(btn_row)

    def _load(self) -> None:
        try:
            with open(self._notes_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and "text" in data:
                self.notes_edit.setPlainText(data["text"])
        except (OSError, ValueError):
            pass

    def _save(self) -> None:
        atomic_json_write(self._notes_path, {"text": self.notes_edit.toPlainText()})

    def _clear(self) -> None:
        self.notes_edit.clear()
        self._save()

    def closeEvent(self, event) -> None:
        self._save()
        super().closeEvent(event)
