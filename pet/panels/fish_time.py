# -*- coding: utf-8 -*-
"""摸鱼计时器面板：记录今天摸鱼时长和效率统计。"""
from __future__ import annotations

import json
import os
import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from ..config import app_dir
from ..styles import (
    CJK_FONT, LABEL_CSS, STAT_CSS, HINT_CSS, BTN_CSS, atomic_json_write,
)
from .base import BasePanel

DISPLAY_CSS = (
    "QLabel { color: #ffb86c; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', monospace; }"
)
DISPLAY_ACTIVE_CSS = (
    "QLabel { color: #57e389; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', monospace; }"
)
FISH_BTN_CSS = BTN_CSS + (
    "QPushButton#resetBtn { background: rgba(255,255,255,0.12); color: #cfc9f2;"
    "border: 1px solid rgba(255,255,255,0.18); }"
)

_FISH_FILE = "fish_time.json"


class FishTimePanel(BasePanel):
    """摸鱼计时器面板。"""

    def __init__(self, parent=None):
        super().__init__(parent, title="摸鱼计时器", width=280, height=340)
        self._data_path = os.path.join(app_dir(), _FISH_FILE)
        self._running = False
        self._is_fish = True
        self._fish_seconds = 0
        self._work_seconds = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._load_today()

    def _build_content(self, lay: QVBoxLayout) -> None:
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(6)

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
        self.start_btn.setStyleSheet(FISH_BTN_CSS)
        self.start_btn.clicked.connect(self._toggle)
        self.switch_btn = QPushButton("切换工作")
        self.switch_btn.setObjectName("resetBtn")
        self.switch_btn.setStyleSheet(FISH_BTN_CSS)
        self.switch_btn.clicked.connect(self._switch_mode)
        self.switch_btn.setEnabled(False)
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setObjectName("resetBtn")
        self.reset_btn.setStyleSheet(FISH_BTN_CSS)
        self.reset_btn.clicked.connect(self._reset)
        btn_row.addWidget(self.start_btn)
        btn_row.addWidget(self.switch_btn)
        btn_row.addWidget(self.reset_btn)
        lay.addLayout(btn_row)

        hint = QLabel("今天也要开心地摸鱼哦~")
        hint.setStyleSheet(HINT_CSS)
        lay.addWidget(hint)

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
        atomic_json_write(self._data_path, {
            "date": today,
            "fish": self._fish_seconds,
            "work": self._work_seconds,
        })

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
