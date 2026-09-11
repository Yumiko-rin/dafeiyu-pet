# -*- coding: utf-8 -*-
"""猜数字小游戏面板。"""
from __future__ import annotations

import random

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QToolButton,
)

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
HINT_CSS = "QLabel { color: #b3aede; font-size: 13px; font-family: " + CJK_FONT + "; }"
MSG_CSS = "QLabel { color: #57e389; font-size: 14px; font-weight: 600; font-family: " + CJK_FONT + "; }"
MSG_ERR_CSS = "QLabel { color: #ff5a6e; font-size: 14px; font-weight: 600; font-family: " + CJK_FONT + "; }"
COUNT_CSS = "QLabel { color: #9a94cf; font-size: 12px; font-family: " + CJK_FONT + "; }"
INPUT_CSS = (
    "QLineEdit { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "padding: 6px 10px; font-size: 14px; font-family: " + CJK_FONT + "; }"
    "QLineEdit:focus { border: 1px solid rgba(140,128,255,0.8); }"
)
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 14px; font-weight: bold; padding: 8px 16px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
    "QPushButton#newBtn { background: rgba(87,227,137,0.8); }"
    "QPushButton#newBtn:hover { background: rgba(87,227,137,1.0); }"
)
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
)


class GuessNumberPanel(QDialog):
    """猜数字小游戏面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("猜数字")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, 260, 280)
        card.setStyleSheet(CARD_CSS)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(10, 6, 60, 160))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        head = QHBoxLayout()
        head.setSpacing(0)
        title = QLabel("猜数字")
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
        guess_btn.setStyleSheet(BTN_CSS)
        guess_btn.clicked.connect(self._guess)
        new_btn = QPushButton("新一局")
        new_btn.setObjectName("newBtn")
        new_btn.setStyleSheet(BTN_CSS)
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

        self._target = random.randint(1, 100)
        self._count = 0
        self._finished = False
        self.hide()

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
            self.msg_label.setText(f"\u2b50 \u606d\u559c\uff01\u7b54\u6848\u5c31\u662f {self._target}\uff0c\u4f60\u53ea\u7528\u4e86 {self._count} \u6b21\uff01")
            self.msg_label.setStyleSheet(MSG_CSS)
            self.hint_label.setText("太厉害了！再来一局？")
        elif num < self._target:
            self.msg_label.setText("太小了，再大一点~")
            self.msg_label.setStyleSheet(MSG_CSS)
        else:
            self.msg_label.setText("太大了，再小一点~")
            self.msg_label.setStyleSheet(MSG_CSS)

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
