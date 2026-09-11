# -*- coding: utf-8 -*-
"""桌面时钟/日历面板：实时时钟 + 月历。"""
from __future__ import annotations

import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QLabel, QVBoxLayout, QWidget, QFrame,
    QGraphicsDropShadowEffect, QCalendarWidget, QHBoxLayout,
    QToolButton,
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
TIME_CSS = (
    "QLabel { color: #f4f2ff; font-size: 42px; font-weight: 700;"
    "font-family: 'Consolas', 'Courier New', monospace; }"
)
DATE_CSS = (
    "QLabel { color: #b3aede; font-size: 14px; font-family: " + CJK_FONT + "; }"
)
WEEKDAY_LABEL_CSS = (
    "QLabel { color: #9a94cf; font-size: 13px; font-family: " + CJK_FONT + "; }"
)
CAL_CSS = (
    "QCalendarWidget { background: rgba(30,26,58,0.9); color: #e0dcf8;"
    "border: none; font-family: " + CJK_FONT + "; }"
    "QCalendarWidget QToolButton { color: #cfc9f2; background: rgba(148,130,255,0.15);"
    "border-radius: 6px; padding: 4px 8px; font-family: " + CJK_FONT + "; }"
    "QCalendarWidget QToolButton:hover { background: rgba(148,130,255,0.35); }"
    "QCalendarWidget QToolButton#qt_calendar_prevmonth,"
    "QCalendarWidget QToolButton#qt_calendar_nextmonth { qproperty-icon: none; min-width: 28px; }"
    "QCalendarWidget QToolButton#qt_calendar_prevmonth { qproperty-text: '<'; }"
    "QCalendarWidget QToolButton#qt_calendar_nextmonth { qproperty-text: '>'; }"
    "QCalendarWidget QToolButton#qt_calendar_monthbutton { font-size: 13px; }"
    "QCalendarWidget QToolButton#qt_calendar_yearbutton { font-size: 13px; }"
    "QCalendarWidget QToolButton#qt_calendar_monthbutton:hover,"
    "QCalendarWidget QToolButton#qt_calendar_yearbutton:hover { background: rgba(148,130,255,0.35); }"
    "QCalendarWidget QWidget#qt_calendar_navigationbar { background: rgba(42,38,78,0.95);"
    "border-bottom: 1px solid rgba(148,130,255,0.25); }"
    "QCalendarWidget QAbstractItemView { background: rgba(30,26,58,0.9); color: #e0dcf8;"
    "selection-background-color: rgba(111,108,255,0.6); selection-color: white;"
    "border: none; font-size: 13px; }"
    "QCalendarWidget QAbstractItemView:enabled { color: #e0dcf8; }"
    "QCalendarWidget QAbstractItemView:disabled { color: rgba(180,170,220,0.4); }"
)
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
)

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class ClockCalendarPanel(QDialog):
    """桌面时钟 + 日历面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("时钟日历")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, 280, 380)
        card.setStyleSheet(CARD_CSS)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(10, 6, 60, 160))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)

        # 标题行（含关闭按钮）
        head = QHBoxLayout()
        head.setSpacing(0)
        title = QLabel("时钟日历")
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

        self.time_label = QLabel("--:--:--")
        self.time_label.setStyleSheet(TIME_CSS)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.time_label)

        self.date_label = QLabel("")
        self.date_label.setStyleSheet(DATE_CSS)
        self.date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.date_label)

        self.weekday_label = QLabel("")
        self.weekday_label.setStyleSheet(WEEKDAY_LABEL_CSS)
        self.weekday_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.weekday_label)

        self.cal = QCalendarWidget()
        self.cal.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.cal.setFixedSize(250, 190)
        self.cal.setStyleSheet(CAL_CSS)
        lay.addWidget(self.cal, 1, Qt.AlignmentFlag.AlignCenter)

        self.hide()
        self._tick()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _tick(self) -> None:
        now = datetime.datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%Y年%m月%d日"))
        wd = WEEKDAYS[now.weekday()]
        self.weekday_label.setText(wd)

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
