# -*- coding: utf-8 -*-
"""系统监控面板：CPU / 内存 / 磁盘 / 网络实时显示。"""
from __future__ import annotations

import psutil

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QVBoxLayout, QWidget, QToolButton,
)
from PySide6.QtGui import QPainter

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
LABEL_CSS = "QLabel { color: #b3aede; font-size: 12px; font-family: " + CJK_FONT + "; }"
VALUE_CSS = "QLabel { color: #f4f2ff; font-size: 13px; font-weight: 600; font-family: " + CJK_FONT + "; }"
BAR_BG = "rgba(255,255,255,0.08)"
BAR_CPU = (111, 108, 255)
BAR_MEM = (79, 139, 255)
BAR_DSK = (87, 227, 137)
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
)


class ProgressBar(QWidget):
    """简洁的进度条组件。"""

    def __init__(self, color=BAR_CPU, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._color = color
        self.setFixedHeight(14)
        self.setMinimumWidth(120)

    def setValue(self, v: float) -> None:
        self._value = max(0.0, min(100.0, v))
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(*BAR_BG))
        p.drawRoundedRect(0, 0, w, h, h / 2, h / 2)
        fw = int(w * self._value / 100)
        if fw > 0:
            r, g, b = self._color
            p.setBrush(QColor(r, g, b, 220))
            p.drawRoundedRect(0, 0, fw, h, h / 2, h / 2)
        p.setPen(QColor(244, 242, 255))
        p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._value:.1f}%")


def _fmt_bytes(b: float) -> str:
    for u in ("B", "KB", "MB", "GB", "TB"):
        if abs(b) < 1024:
            return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} PB"


class SystemMonitorPanel(QDialog):
    """系统监控面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("系统监控")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, 280, 290)
        card.setStyleSheet(CARD_CSS)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(10, 6, 60, 160))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(0)
        title = QLabel("系统监控")
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

        def make_row(label_text: str, color=BAR_CPU):
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl = QLabel(label_text)
            lbl.setStyleSheet(LABEL_CSS)
            lbl.setFixedWidth(40)
            bar = ProgressBar(color)
            val = QLabel("--")
            val.setStyleSheet(VALUE_CSS)
            val.setFixedWidth(60)
            val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(lbl)
            row.addWidget(bar, 1)
            row.addWidget(val)
            return row, bar, val

        self.cpu_row, self.cpu_bar, self.cpu_val = make_row("CPU", BAR_CPU)
        self.mem_row, self.mem_bar, self.mem_val = make_row("内存", BAR_MEM)
        self.dsk_row, self.dsk_bar, self.dsk_val = make_row("磁盘", BAR_DSK)
        lay.addLayout(self.cpu_row)
        lay.addLayout(self.mem_row)
        lay.addLayout(self.dsk_row)

        net_title = QLabel("网络流量")
        net_title.setStyleSheet(LABEL_CSS)
        lay.addWidget(net_title)
        net_row = QHBoxLayout()
        net_row.setSpacing(12)
        self.up_lbl = QLabel("↑ 0 KB/s")
        self.up_lbl.setStyleSheet(VALUE_CSS)
        self.down_lbl = QLabel("↓ 0 KB/s")
        self.down_lbl.setStyleSheet(VALUE_CSS)
        net_row.addWidget(self.up_lbl)
        net_row.addWidget(self.down_lbl)
        net_row.addStretch(1)
        lay.addLayout(net_row)

        lay.addStretch(1)

        self._net_prev = psutil.net_io_counters()
        self._timer = QTimer(self)
        self._timer.setInterval(1500)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self.hide()
        self._tick()

    def _tick(self) -> None:
        self.cpu_bar.setValue(psutil.cpu_percent(interval=None))
        self.cpu_val.setText(f"{psutil.cpu_percent():.1f}%")
        mem = psutil.virtual_memory()
        self.mem_bar.setValue(mem.percent)
        self.mem_val.setText(_fmt_bytes(mem.used))
        try:
            dsk = psutil.disk_usage("/")
            self.dsk_bar.setValue(dsk.percent)
            self.dsk_val.setText(_fmt_bytes(dsk.used))
        except Exception:
            self.dsk_bar.setValue(0)
            self.dsk_val.setText("--")
        cur = psutil.net_io_counters()
        dt = 1.5
        up = (cur.bytes_sent - self._net_prev.bytes_sent) / dt
        down = (cur.bytes_recv - self._net_prev.bytes_recv) / dt
        self._net_prev = cur
        self.up_lbl.setText(f"↑ {_fmt_bytes(up)}/s")
        self.down_lbl.setText(f"↓ {_fmt_bytes(down)}/s")

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
