# -*- coding: utf-8 -*-
"""猜数字小游戏面板。"""
from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from ..styles import CJK_FONT, INPUT_CSS, BTN_CSS
from .base import BasePanel

HINT_CSS = "QLabel { color: #b3aede; font-size: 13px; font-family: " + CJK_FONT + "; }"
MSG_CSS = "QLabel { color: #57e389; font-size: 14px; font-weight: 600; font-family: " + CJK_FONT + "; }"
MSG_ERR_CSS = "QLabel { color: #ff5a6e; font-size: 14px; font-weight: 600; font-family: " + CJK_FONT + "; }"
COUNT_CSS = "QLabel { color: #9a94cf; font-size: 12px; font-family: " + CJK_FONT + "; }"
NEW_BTN_CSS = BTN_CSS + (
    "QPushButton#newBtn { background: rgba(87,227,137,0.8); }"
    "QPushButton#newBtn:hover { background: rgba(87,227,137,1.0); }"
)


class GuessNumberPanel(BasePanel):
    """猜数字小游戏面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, title="猜数字", width=260, height=280)
        self._target = random.randint(1, 100)
        self._count = 0
        self._finished = False

    def _build_content(self, lay: QVBoxLayout) -> None:
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        self.hint_label = QLabel("我想了一个 1~100 的数字，猜猜看？")
        self.hint_label.setStyleSheet(HINT_CSS)
        self.hint_label.setWordWrap(True)
        lay.addWidget(self.hint_label)

        self.guess_input = QLineEdit()
        self.guess_input.setPlaceholderText("输入你的猜测...")
        self.guess_input.setStyleSheet(INPUT_CSS)
        self.guess_input.returnPressed.connect(self._guess)
        lay.addWidget(self.guess_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        guess_btn = QPushButton("猜!")
        guess_btn.setStyleSheet(NEW_BTN_CSS)
        guess_btn.clicked.connect(self._guess)
        new_btn = QPushButton("新一局")
        new_btn.setObjectName("newBtn")
        new_btn.setStyleSheet(NEW_BTN_CSS)
        new_btn.clicked.connect(self._new_game)
        btn_row.addWidget(guess_btn)
        btn_row.addWidget(new_btn)
        lay.addLayout(btn_row)

        self.msg_label = QLabel("")
        self.msg_label.setStyleSheet(MSG_CSS)
        self.msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.msg_label.setWordWrap(True)
        lay.addWidget(self.msg_label)

        self.count_label = QLabel("已猜 0 次")
        self.count_label.setStyleSheet(COUNT_CSS)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.count_label)

        lay.addStretch(1)

    def _new_game(self) -> None:
        self._target = random.randint(1, 100)
        self._count = 0
        self._finished = False
        self.guess_input.clear()
        self.msg_label.setText("")
        self.msg_label.setStyleSheet(MSG_CSS)
        self.count_label.setText("已猜 0 次")
        self.hint_label.setText("我想了一个 1~100 的数字，猜猜看？")

    def _guess(self) -> None:
        if self._finished:
            return
        text = self.guess_input.text().strip()
        if not text:
            return
        try:
            num = int(text)
        except ValueError:
            self.msg_label.setText("请输入有效数字！")
            self.msg_label.setStyleSheet(MSG_ERR_CSS)
            return
        self._count += 1
        self.count_label.setText(f"已猜 {self._count} 次")
        self.guess_input.clear()

        if num == self._target:
            self._finished = True
            self.msg_label.setText(
                f"\u2b50 恭喜！答案就是 {self._target}，你只用了 {self._count} 次！"
            )
            self.msg_label.setStyleSheet(MSG_CSS)
            self.hint_label.setText("太厉害了！再来一局？")
        elif num < self._target:
            self.msg_label.setText("太小了，再大一点~")
            self.msg_label.setStyleSheet(MSG_CSS)
        else:
            self.msg_label.setText("太大了，再小一点~")
            self.msg_label.setStyleSheet(MSG_CSS)
