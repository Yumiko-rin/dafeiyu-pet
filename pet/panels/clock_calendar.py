# -*- coding: utf-8 -*-
"""桌面时钟/日历面板：实时时钟 + 月历。"""
from __future__ import annotations

import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QCalendarWidget, QHBoxLayout, QLabel, QVBoxLayout

from ..styles import CJK_FONT, LABEL_CSS, HINT_CSS
from .base import BasePanel

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

WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


class ClockCalendarPanel(BasePanel):
    """桌面时钟 + 日历面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, title="时钟日历", width=280, height=380)
        self._tick()
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()

    def _build_content(self, lay: QVBoxLayout) -> None:
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

    def _tick(self) -> None:
        now = datetime.datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%Y年%m月%d日"))
        wd = WEEKDAYS[now.weekday()]
        self.weekday_label.setText(wd)
