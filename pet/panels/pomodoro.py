# -*- coding: utf-8 -*-
"""番茄钟面板：工作 25 分钟 / 休息 5 分钟。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QPushButton, QVBoxLayout, QToolButton,
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
STATUS_CSS = "QLabel { color: #b3aede; font-size: 13px; font-family: " + CJK_FONT + "; }"
DISPLAY_CSS = (
    "QLabel { color: #57e389; font-size: 56px; font-weight: 700;"
    "font-family: 'Consolas', 'Courier New', monospace; }"
)
DISPLAY_REST_CSS = (
    "QLabel { color: #ffb86c; font-size: 56px; font-weight: 700;"
    "font-family: 'Consolas', 'Courier New', monospace; }"
)
COUNT_CSS = "QLabel { color: #9a94cf; font-size: 12px; font-family: " + CJK_FONT + "; }"
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 14px; font-weight: bold; padding: 8px 16px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
    "QPushButton:disabled { background: rgba(120,120,160,0.5); }"
    "QPushButton#resetBtn { background: rgba(255,255,255,0.12); color: #cfc9f2;"
    "border: 1px solid rgba(255,255,255,0.18); }"
)
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
)

WORK_SECONDS = 25 * 60
REST_SECONDS = 5 * 60


class PomodoroPanel(QDialog):
    """番茄钟面板。"""
    pomodoro_done = Signal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("番茄钟")
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
        title = QLabel("番茄钟")
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
        self.start_btn.setStyleSheet(BTN_CSS)
        self.start_btn.clicked.connect(self._toggle)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setStyleSheet(BTN_CSS)
        self.reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reset_btn)
        lay.addLayout(btn_row)

        self._running = False
        self._is_work = True
        self._remaining = WORK_SECONDS
        self._completed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self.hide()

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

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
