# -*- coding: utf-8 -*-
"""番茄钟面板：工作 25 分钟 / 休息 5 分钟。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ..styles import CJK_FONT, STAT_CSS, DISPLAY_CSS, DISPLAY_REST_CSS, BTN_CSS
from .base import BasePanel

STATUS_CSS = "QLabel { color: #b3aede; font-size: 13px; font-family: " + CJK_FONT + "; }"
COUNT_CSS = "QLabel { color: #9a94cf; font-size: 12px; font-family: " + CJK_FONT + "; }"
POMODORO_BTN_CSS = BTN_CSS + (
    "QPushButton#resetBtn { background: rgba(255,255,255,0.12); color: #cfc9f2;"
    "border: 1px solid rgba(255,255,255,0.18); }"
)

WORK_SECONDS = 25 * 60
REST_SECONDS = 5 * 60


class PomodoroPanel(BasePanel):
    """番茄钟面板。"""
    pomodoro_done = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, title="番茄钟", width=260, height=280)
        self._running = False
        self._is_work = True
        self._remaining = WORK_SECONDS
        self._completed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    def _build_content(self, lay: QVBoxLayout) -> None:
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(8)

        self.status_label = QLabel("专注模式")
        self.status_label.setStyleSheet(STATUS_CSS)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status_label)

        self.display = QLabel("25:00")
        self.display.setStyleSheet(DISPLAY_CSS)
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.display)

        self.count_label = QLabel("已完成 0 轮")
        self.count_label.setStyleSheet(COUNT_CSS)
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.count_label)

        lay.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.start_btn = QPushButton("开始专注")
        self.start_btn.setStyleSheet(POMODORO_BTN_CSS)
        self.start_btn.clicked.connect(self._toggle)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setStyleSheet(POMODORO_BTN_CSS)
        self.reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reset_btn)
        lay.addLayout(btn_row)

    def _toggle(self) -> None:
        if self._running:
            self._running = False
            self.start_btn.setText("继续")
            self._timer.stop()
        else:
            self._running = True
            self.start_btn.setText("暂停")
            self._timer.start()

    def _reset(self) -> None:
        self._running = False
        self._is_work = True
        self._remaining = WORK_SECONDS
        self.start_btn.setText("开始专注")
        self._timer.stop()
        self.status_label.setText("专注模式")
        self.display.setStyleSheet(DISPLAY_CSS)
        self._update_display()

    def _tick(self) -> None:
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            if self._is_work:
                self._completed += 1
                self.count_label.setText(f"已完成 {self._completed} 轮")
                self.pomodoro_done.emit()
                self._is_work = False
                self._remaining = REST_SECONDS
                self.status_label.setText("休息一下~")
                self.display.setStyleSheet(DISPLAY_REST_CSS)
            else:
                self._is_work = True
                self._remaining = WORK_SECONDS
                self.status_label.setText("专注模式")
                self.display.setStyleSheet(DISPLAY_CSS)
            self._running = False
            self.start_btn.setText("开始专注")
        self._update_display()

    def _update_display(self) -> None:
        m = self._remaining // 60
        s = self._remaining % 60
        self.display.setText(f"{m:02d}:{s:02d}")
