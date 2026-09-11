# -*- coding: utf-8 -*-
"""剪贴板历史面板：记录复制过的文本，方便回溯。"""
from __future__ import annotations

import json
import os
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QClipboard
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

from ..config import app_dir
from ..styles import HINT_CSS, LIST_CSS, BTN_CSS, atomic_json_write
from .base import BasePanel

_CLIP_FILE = "clipboard_history.json"
_MAX_ITEMS = 50

CLIP_BTN_CSS = BTN_CSS + (
    "QPushButton#delBtn { background: rgba(255,90,110,0.7); }"
    "QPushButton#delBtn:hover { background: rgba(255,90,110,1.0); }"
)


class ClipboardHistoryPanel(BasePanel):
    """剪贴板历史面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, title="剪贴板历史", width=300, height=350)
        self._clip_path = os.path.join(app_dir(), _CLIP_FILE)
        self._history = []
        self._load()
        self._last_clip = ""
        self._timer = QTimer(self)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self._check_clip)
        self._timer.start()

    def _build_content(self, lay: QVBoxLayout) -> None:
        lay.setSpacing(8)

        self.clip_list = QListWidget()
        self.clip_list.setStyleSheet(LIST_CSS)
        self.clip_list.itemDoubleClicked.connect(self._copy_item)
        lay.addWidget(self.clip_list, 1)

        hint = QLabel("双击条目可重新复制")
        hint.setStyleSheet(HINT_CSS)
        lay.addWidget(hint)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        paste_btn = QPushButton("粘贴当前剪贴板")
        paste_btn.setStyleSheet(CLIP_BTN_CSS)
        paste_btn.clicked.connect(self._capture)
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("delBtn")
        clear_btn.setStyleSheet(CLIP_BTN_CSS)
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        lay.addLayout(btn_row)

    def _load(self) -> None:
        try:
            with open(self._clip_path, "r", encoding="utf-8") as f:
                self._history = json.load(f)
            if not isinstance(self._history, list):
                self._history = []
        except (OSError, ValueError):
            self._history = []
        self._refresh_list()

    def _persist(self) -> None:
        atomic_json_write(self._clip_path, self._history[-_MAX_ITEMS:])

    def _refresh_list(self) -> None:
        self.clip_list.clear()
        for item in reversed(self._history):
            text = item.get("text", "")[:80].replace("\n", " ")
            ts = item.get("time", "")
            self.clip_list.addItem(f"[{ts}] {text}")

    def _check_clip(self) -> None:
        try:
            clip = QApplication.clipboard()
            text = clip.text(QClipboard.Mode.Clipboard) if clip else ""
            if text and text != self._last_clip and len(text.strip()) > 0:
                self._last_clip = text
                ts = time.strftime("%H:%M:%S")
                self._history.append({"text": text[:500], "time": ts})
                if len(self._history) > _MAX_ITEMS:
                    self._history = self._history[-_MAX_ITEMS:]
                self._refresh_list()
                self._persist()
        except Exception:
            pass

    def _capture(self) -> None:
        self._last_clip = ""
        self._check_clip()

    def _copy_item(self, item: QListWidgetItem) -> None:
        row = self.clip_list.row(item)
        idx = len(self._history) - 1 - row
        if 0 <= idx < len(self._history):
            text = self._history[idx].get("text", "")
            clip = QApplication.clipboard()
            if clip:
                clip.setText(text, QClipboard.Mode.Clipboard)
                self._last_clip = text

    def _clear(self) -> None:
        self._history.clear()
        self._refresh_list()
        self._persist()
