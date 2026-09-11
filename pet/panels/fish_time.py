# -*- coding: utf-8 -*-
"""摸鱼计时器面板：记录今天摸鱼时长和效率统计。"""
from __future__ import annotations

import json
import os
import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QPushButton, QVBoxLayout, QToolButton,
)

from ..config import app_dir

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
DISPLAY_CSS = (
    "QLabel { color: #ffb86c; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', monospace; }"
)
DISPLAY_ACTIVE_CSS = (
    "QLabel { color: #57e389; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', monospace; }"
)
LABEL_CSS = "QLabel { color: #b3aede; font-size: 13px; font-family: " + CJK_FONT + "; }"
STAT_CSS = "QLabel { color: #f4f2ff; font-size: 14px; font-weight: 600; font-family: " + CJK_FONT + "; }"
HINT_CSS = "QLabel { color: #9a94cf; font-size: 11px; font-family: " + CJK_FONT + "; }"
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 14px; font-weight: bold; padding: 10px 16px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
    "QPushButton#resetBtn { background: rgba(255,255,255,0.12); color: #cfc9f2;"
    "border: 1px solid rgba(255,255,255,0.18); }"
)
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
)

_FISH_FILE = "fish_time.json"


class FishTimePanel(QDialog):
    """摸鱼计时器面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("摸鱼计时器")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        card = QFrame(self)
        card.setObjectName("card")
        card.setGeometry(0, 0, 280, 340)
        card.setStyleSheet(CARD_CSS)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(10, 6, 60, 160))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(6)

        head = QHBoxLayout()
        head.setSpacing(0)
        title = QLabel("摸鱼计时器")
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

        self.status_label = QLabel("暂停中")
        self.status_label.setStyleSheet(LABEL_CSS)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.status_label)

        self.display = QLabel("00:00:00")
        self.display.setStyleSheet(DISPLAY_CSS)
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.display)

        lay.addSpacing(4)

        stats_title = QLabel("今日统计")
        stats_title.setStyleSheet(LABEL_CSS)
        lay.addWidget(stats_title)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)
        for label_text in ("摸鱼时长", "有效工作", "效率"):
            box = QVBoxLayout()
            box.setSpacing(2)
            lbl = QLabel(label_text)
            lbl.setStyleSheet(LABEL_CSS)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val = QLabel("0h 0m")
            val.setStyleSheet(STAT_CSS)
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            box.addWidget(lbl)
            box.addWidget(val)
            stats_row.addLayout(box)
        self.fish_stat = stats_row.itemAt(0).itemAt(1).widget()
        self.work_stat = stats_row.itemAt(1).itemAt(1).widget()
        self.eff_stat = stats_row.itemAt(2).itemAt(1).widget()
        lay.addLayout(stats_row)

        lay.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.start_btn = QPushButton("开始摸鱼")
        self.start_btn.setStyleSheet(BTN_CSS)
        self.start_btn.clicked.connect(self._toggle)
        self.switch_btn = QPushButton("切换工作")
        self.switch_btn.setObjectName("resetBtn")
        self.switch_btn.setStyleSheet(BTN_CSS)
        self.switch_btn.clicked.connect(self._switch_mode)
        self.switch_btn.setEnabled(False)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setStyleSheet(BTN_CSS)
        self.reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.switch_btn)
        btn_row.addWidget(self.reset_btn)
        lay.addLayout(btn_row)

        hint = QLabel("今天也要开心地摸鱼哦~")
        hint.setStyleSheet(HINT_CSS)
        lay.addWidget(hint)

        self._data_path = os.path.join(app_dir(), _FISH_FILE)
        self._running = False
        self._is_fish = True
        self._fish_seconds = 0
        self._work_seconds = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._load_today()
        self.hide()

    def _load_today(self) -> None:
        today = datetime.date.today().isoformat()
        try:
            with open(self._data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and data.get("date") == today:
                self._fish_seconds = data.get("fish", 0)
                self._work_seconds = data.get("work", 0)
        except (OSError, ValueError):
            pass
        self._update_stats()

    def _persist(self) -> None:
        today = datetime.date.today().isoformat()
        try:
            with open(self._data_path, "w", encoding="utf-8") as f:
                json.dump({
                    "date": today,
                    "fish": self._fish_seconds,
                    "work": self._work_seconds,
                }, f)
        except OSError:
            pass

    def _toggle(self) -> None:
        if self._running:
            self._running = False
            self.start_btn.setText("继续摸鱼" if self._is_fish else "继续工作")
            self.status_label.setText("暂停中")
            self.display.setStyleSheet(DISPLAY_CSS)
            self.switch_btn.setEnabled(False)
            self._timer.stop()
        else:
            self._running = True
            self.start_btn.setText("停止")
            self.status_label.setText("摸鱼中..." if self._is_fish else "工作中...")
            self.display.setStyleSheet(DISPLAY_ACTIVE_CSS)
            self.switch_btn.setEnabled(True)
            self._timer.start()

    def _switch_mode(self) -> None:
        if not self._running:
            return
        self._is_fish = not self._is_fish
        if self._is_fish:
            self.status_label.setText("摸鱼中...")
            self.switch_btn.setText("切换工作")
        else:
            self.status_label.setText("工作中...")
            self.switch_btn.setText("切换摸鱼")

    def _reset(self) -> None:
        self._running = False
        self._is_fish = True
        self._fish_seconds = 0
        self._work_seconds = 0
        self.start_btn.setText("开始摸鱼")
        self.switch_btn.setText("切换工作")
        self.switch_btn.setEnabled(False)
        self.status_label.setText("暂停中")
        self.display.setStyleSheet(DISPLAY_CSS)
        self._timer.stop()
        self._update_stats()
        self._persist()

    def _tick(self) -> None:
        if self._is_fish:
            self._fish_seconds += 1
        else:
            self._work_seconds += 1
        self._update_display()
        self._update_stats()
        if (self._fish_seconds + self._work_seconds) % 30 == 0:
            self._persist()

    def _update_display(self) -> None:
        total = self._fish_seconds if self._is_fish else self._work_seconds
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        self.display.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _update_stats(self) -> None:
        fh = self._fish_seconds // 3600
        fm = (self._fish_seconds % 3600) // 60
        self.fish_stat.setText(f"{fh}h {fm}m")
        wh = self._work_seconds // 3600
        wm = (self._work_seconds % 3600) // 60
        self.work_stat.setText(f"{wh}h {wm}m")
        total = self._fish_seconds + self._work_seconds
        if total > 0:
            eff = self._work_seconds / total * 100
            self.eff_stat.setText(f"{eff:.0f}%")
        else:
            self.eff_stat.setText("--")

    def closeEvent(self, event) -> None:
        self._persist()
        super().closeEvent(event)

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
