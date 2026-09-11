# -*- coding: utf-8 -*-
"""剪贴板历史面板：记录复制过的文本，方便回溯。"""
from __future__ import annotations

import json
import os
import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QClipboard
from PySide6.QtWidgets import (
    QApplication, QDialog, QFrame, QGraphicsDropShadowEffect,
    QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
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

_CLIP_FILE = "clipboard_history.json"
_MAX_ITEMS = 50


class ClipboardHistoryPanel(QDialog):
    """剪贴板历史面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("剪贴板历史")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, 300, 350)
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
        title = QLabel("剪贴板历史")
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
        paste_btn.setStyleSheet(BTN_CSS)
        paste_btn.clicked.connect(self._capture)
        clear_btn = QPushButton("清空")
        clear_btn.setObjectName("delBtn")
        clear_btn.setStyleSheet(BTN_CSS)
        clear_btn.clicked.connect(self._clear)
        btn_row.addWidget(paste_btn)
        btn_row.addWidget(clear_btn)
        lay.addLayout(btn_row)

        self._clip_path = os.path.join(app_dir(), _CLIP_FILE)
        self._history = []
        self._load()
        self._last_clip = ""
        self._timer = QTimer(self)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self._check_clip)
        self._timer.start()
        self.hide()

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
        try:
            with open(self._clip_path, "w", encoding="utf-8") as f:
                json.dump(self._history[-_MAX_ITEMS:], f, ensure_ascii=False)
        except OSError:
            pass

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

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
