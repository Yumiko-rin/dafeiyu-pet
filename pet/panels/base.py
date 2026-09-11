# -*- coding: utf-8 -*-
"""基类面板：所有功能面板的公共基类，消除样板代码。"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QVBoxLayout, QToolButton,
)

from .styles import CARD_CSS, TITLE_CSS, CLOSE_CSS


class BasePanel(QDialog):
    """所有功能面板的基类。

    子类只需实现 _build_content(lay) 方法，将内容添加到 lay 中即可。
    """

    def __init__(self, parent=None, title: str = "", width: int = 280, height: int = 320):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setWindowTitle(title)
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, width, height)
        card.setStyleSheet(CARD_CSS)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(10, 6, 60, 160))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)

        # 标题行（含关闭按钮）
        head = QHBoxLayout()
        head.setSpacing(0)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(TITLE_CSS)
        head.addWidget(title_lbl)
        head.addStretch(1)
        close_btn = QToolButton()
        close_btn.setText("\u2715")
        close_btn.setFixedSize(26, 26)
        close_btn.setStyleSheet(CLOSE_CSS)
        close_btn.clicked.connect(self.hide)
        head.addWidget(close_btn)
        lay.addLayout(head)

        self._lay = lay
        self.hide()

    def _add_stretch(self) -> None:
        self._lay.addStretch(1)

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
