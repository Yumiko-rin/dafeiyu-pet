# -*- coding: utf-8 -*-
"""倒计时/提醒面板。"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QSpinBox, QWidget,
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
LABEL_CSS = "QLabel { color: #cfc9f2; font-size: 13px; font-family: " + CJK_FONT + "; }"
TITLE_CSS = "QLabel { color: #f4f2ff; font-size: 15px; font-weight: 600; font-family: " + CJK_FONT + "; }"
DISPLAY_CSS = (
    "QLabel { color: #57e389; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', 'Courier New', monospace; }"
)
INPUT_CSS = (
    "QLineEdit { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "padding: 6px 10px; font-size: 13px; font-family: " + CJK_FONT + "; }"
    "QLineEdit:focus { border: 1px solid rgba(140,128,255,0.8); }"
)
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 14px; font-weight: bold; padding: 8px 16px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
    "QPushButton:disabled { background: rgba(120,120,160,0.5); }"
    "QPushButton#stopBtn { background: rgba(255,90,110,0.8); }"
    "QPushButton#stopBtn:hover { background: rgba(255,90,110,1.0); }"
)
SPIN_CSS = (
    "QSpinBox { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 8px;"
    "padding: 4px; font-size: 14px; font-family: " + CJK_FONT + "; }"
    "QSpinBox::up-button, QSpinBox::down-button { width: 20px; }"
)
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
)


class CountdownPanel(QDialog):
    """倒计时/提醒面板。"""
    alarm = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("倒计时提醒")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, 280, 320)
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
        title = QLabel("倒计时提醒")
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
        self.start_btn.setStyleSheet(BTN_CSS)
        self.start_btn.clicked.connect(self._toggle)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setStyleSheet(BTN_CSS)
        self.reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.reset_btn)
        lay.addLayout(btn_row)

        self._running = False
        self._remaining = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self.hide()

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
            self.display.setStyleSheet(
                "QLabel { color: #ff5a6e; font-size: 48px; font-weight: 700;"
                "font-family: 'Consolas', monospace; }"
            )
            self.display.setText("时间到!")
            msg = self.msg_edit.text().strip() or "倒计时结束！"
            self.alarm.emit(msg)
            return
        h = self._remaining // 3600
        m = (self._remaining % 3600) // 60
        s = self._remaining % 60
        self.display.setText(f"{h:02d}:{m:02d}:{s:02d}")
        self._remaining -= 1

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
