# -*- coding: utf-8 -*-
"""倒计时/提醒面板。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QSpinBox, QVBoxLayout,
)

from ..styles import (
    CJK_FONT, LABEL_CSS, DISPLAY_CSS, INPUT_CSS, BTN_CSS, SPIN_CSS,
)
from .base import BasePanel

DISPLAY_ALARM_CSS = (
    "QLabel { color: #ff5a6e; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', monospace; }"
)
BTN_STOP_CSS = BTN_CSS + (
    "QPushButton#stopBtn { background: rgba(255,90,110,0.8); }"
    "QPushButton#stopBtn:hover { background: rgba(255,90,110,1.0); }"
)


class CountdownPanel(BasePanel):
    """倒计时/提醒面板。"""
    alarm = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, title="倒计时提醒", width=280, height=320)

    def _build_content(self, lay: QVBoxLayout) -> None:
        lay.setSpacing(8)

        row1 = QHBoxLayout()
        row1.setSpacing(6)
        lbl1 = QLabel("时")
        lbl1.setStyleSheet(LABEL_CSS)
        self.h_spin = QSpinBox()
        self.h_spin.setRange(0, 23)
        self.h_spin.setStyleSheet(SPIN_CSS)
        lbl2 = QLabel("分")
        lbl2.setStyleSheet(LABEL_CSS)
        self.m_spin = QSpinBox()
        self.m_spin.setRange(0, 59)
        self.m_spin.setValue(25)
        self.m_spin.setStyleSheet(SPIN_CSS)
        lbl3 = QLabel("秒")
        lbl3.setStyleSheet(LABEL_CSS)
        self.s_spin = QSpinBox()
        self.s_spin.setRange(0, 59)
        self.s_spin.setStyleSheet(SPIN_CSS)
        row1.addWidget(lbl1)
        row1.addWidget(self.h_spin)
        row1.addWidget(lbl2)
        row1.addWidget(self.m_spin)
        row1.addWidget(lbl3)
        row1.addWidget(self.s_spin)
        lay.addLayout(row1)

        msg_row = QHBoxLayout()
        msg_lbl = QLabel("提醒内容")
        msg_lbl.setStyleSheet(LABEL_CSS)
        self.msg_edit = QLineEdit()
        self.msg_edit.setPlaceholderText("到时间啦！")
        self.msg_edit.setStyleSheet(INPUT_CSS)
        msg_row.addWidget(msg_lbl)
        msg_row.addWidget(self.msg_edit, 1)
        lay.addLayout(msg_row)

        self.display = QLabel("00:00:00")
        self.display.setStyleSheet(DISPLAY_CSS)
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.display)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.start_btn = QPushButton("开始")
        self.start_btn.setStyleSheet(BTN_STOP_CSS)
        self.start_btn.clicked.connect(self._toggle)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setStyleSheet(BTN_STOP_CSS)
        self.reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reset_btn)
        lay.addLayout(btn_row)

        self._running = False
        self._remaining = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def _toggle(self) -> None:
        if self._running:
            self._stop()
        else:
            self._start()

    def _start(self) -> None:
        if not self._running:
            if self._remaining == 0:
                total = self.h_spin.value() * 3600 + self.m_spin.value() * 60 + self.s_spin.value()
                if total <= 0:
                    return
                self._remaining = total
            self._running = True
            self.start_btn.setText("暂停")
            self._timer.start()
            self._tick()

    def _stop(self) -> None:
        self._running = False
        self.start_btn.setText("继续")
        self._timer.stop()

    def _reset(self) -> None:
        self._running = False
        self._remaining = 0
        self.start_btn.setText("开始")
        self._timer.stop()
        self.display.setText("00:00:00")
        self.display.setStyleSheet(DISPLAY_CSS)

    def _tick(self) -> None:
        if self._remaining <= 0:
            self._timer.stop()
            self._running = False
            self.start_btn.setText("开始")
            self.display.setStyleSheet(DISPLAY_ALARM_CSS)
            self.display.setText("时间到!")
            msg = self.msg_edit.text().strip() or "倒计时结束！"
            self.alarm.emit(msg)
            return
        h = self._remaining // 3600
        m = (self._remaining % 3600) // 60
        s = self._remaining % 60
        self.display.setText(f"{h:02d}:{m:02d}:{s:02d}")
        self._remaining -= 1
