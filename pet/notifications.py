# -*- coding: utf-8 -*-
"""通知系统：定时检查条件并触发桌宠提醒。"""
from __future__ import annotations

import time

import psutil
from PySide6.QtCore import QTimer, QObject
from typing import Callable


class NotificationManager(QObject):
    """定时检查系统/天气状态，触发回调。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._callbacks: list = []
        self._weather_check_interval = 1800000  # 30分钟
        self._system_check_interval = 10000  # 10秒
        self._last_cpu_warn = 0
        self._last_mem_warn = 0

        self._system_timer = QTimer(self)
        self._system_timer.setInterval(self._system_check_interval)
        self._system_timer.timeout.connect(self._check_system)
        self._system_timer.start()

    def on_notify(self, callback: Callable[[str], None]) -> None:
        self._callbacks.append(callback)

    def _notify(self, msg: str) -> None:
        for cb in self._callbacks:
            try:
                cb(msg)
            except Exception:
                pass

    def _check_system(self) -> None:
        now = int(time.time())

        cpu = psutil.cpu_percent(interval=None)
        if cpu > 90 and now - self._last_cpu_warn > 300:
            self._last_cpu_warn = now
            self._notify(f"CPU 使用率 {cpu:.0f}%，好高哦！")

        mem = psutil.virtual_memory()
        if mem.percent > 85 and now - self._last_mem_warn > 300:
            self._last_mem_warn = now
            self._notify(f"内存使用 {mem.percent:.0f}%，快满了！")

    def check_weather_alert(self, temp_c: int, desc: str) -> None:
        """天气获取后调用，检查极端天气。"""
        temp = int(temp_c) if str(temp_c).lstrip('-').isdigit() else 0
        if temp > 35:
            self._notify(f"好热啊！{temp}°C，记得开空调~")
        elif temp < -10:
            self._notify(f"好冷！{temp}°C，多穿点~")
        if "雨" in desc or "rain" in desc.lower():
            self._notify(f"要下雨了，记得带伞~")
        if "雪" in desc or "snow" in desc.lower():
            self._notify(f"下雪啦！注意保暖~")
