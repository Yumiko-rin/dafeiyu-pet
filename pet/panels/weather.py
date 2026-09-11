# -*- coding: utf-8 -*-
"""天气显示面板：通过 wttr.in 获取天气信息（带缓存）。"""
from __future__ import annotations

import time
import threading

import requests

from ..logger import log
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from ..styles import CJK_FONT, INPUT_CSS, HINT_CSS
from .base import BasePanel

TEMP_CSS = (
    "QLabel { color: #f4f2ff; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', monospace; }"
)
DETAIL_CSS = "QLabel { color: #b3aede; font-size: 13px; font-family: " + CJK_FONT + "; }"
DESC_CSS = "QLabel { color: #57e389; font-size: 14px; font-family: " + CJK_FONT + "; }"
FETCH_BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 13px; font-weight: bold; padding: 8px 16px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
)

_WEATHER_ICONS = {
    "Clear": "\u2600\ufe0f", "Sunny": "\u2600\ufe0f",
    "Partly cloudy": "\u26c5", "Cloudy": "\u2601\ufe0f",
    "Overcast": "\u2601\ufe0f", "Mist": "\ud83c\udf2b\ufe0f",
    "Fog": "\ud83c\udf2b\ufe0f",
    "Light rain": "\ud83c\udf26\ufe0f", "Rain": "\ud83c\udf27\ufe0f",
    "Heavy rain": "\u26c8\ufe0f", "Thunderstorm": "\u26c8\ufe0f",
    "Snow": "\u2744\ufe0f", "Light snow": "\ud83c\udf28\ufe0f",
    "Sleet": "\ud83c\udf28\ufe0f",
    "Drizzle": "\ud83c\udf26\ufe0f", "Haze": "\ud83c\udf2b\ufe0f",
}

_WEATHER_CN = {
    "Clear": "晴", "Sunny": "晴",
    "Partly cloudy": "多云", "Cloudy": "阴",
    "Overcast": "阴天", "Mist": "薄雾",
    "Fog": "雾",
    "Light rain": "小雨", "Rain": "中雨",
    "Heavy rain": "大雨", "Thunderstorm": "雷阵雨",
    "Snow": "雪", "Light snow": "小雪",
    "Sleet": "雨夹雪",
    "Drizzle": "毛毛雨", "Haze": "霾",
}

_CACHE_TTL = 1800  # 30 minutes


def _icon_for(desc: str) -> str:
    for k, v in _WEATHER_ICONS.items():
        if k.lower() in desc.lower():
            return v
    return "\ud83c\udf24\ufe0f"


def _cn_desc(desc: str) -> str:
    for k, v in _WEATHER_CN.items():
        if k.lower() in desc.lower():
            return v
    return desc


class WeatherPanel(BasePanel):
    """天气显示面板。"""
    _weather_ready = Signal(dict)

    def __init__(self, parent=None):
        self._cache = {}
        self._cache_time = 0.0
        self._session = requests.Session()
        super().__init__(parent, title="天气", width=280, height=320)
        self._weather_ready.connect(self._on_weather)

    def _build_content(self, lay: QVBoxLayout) -> None:
        lay.setSpacing(6)

        city_row = QHBoxLayout()
        city_row.setSpacing(6)
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("城市名 (如 Beijing / 上海)")
        self.city_edit.setStyleSheet(INPUT_CSS)
        self.city_edit.returnPressed.connect(self._fetch)
        city_row.addWidget(self.city_edit, 1)
        fetch_btn = QPushButton("查询")
        fetch_btn.setStyleSheet(FETCH_BTN_CSS)
        fetch_btn.clicked.connect(self._fetch)
        city_row.addWidget(fetch_btn)
        lay.addLayout(city_row)

        self.icon_label = QLabel("")
        self.icon_label.setStyleSheet("font-size: 42px;")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.icon_label)

        self.temp_label = QLabel("--")
        self.temp_label.setStyleSheet(TEMP_CSS)
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.temp_label)

        self.desc_label = QLabel("")
        self.desc_label.setStyleSheet(DESC_CSS)
        self.desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.desc_label)

        self.detail_label = QLabel("")
        self.detail_label.setStyleSheet(DETAIL_CSS)
        self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label.setWordWrap(True)
        lay.addWidget(self.detail_label)

        lay.addStretch(1)

        self._city = "Beijing"

    def _fetch(self) -> None:
        city = self.city_edit.text().strip() or "Beijing"
        self._city = city
        now = time.time()
        cache_key = city.lower()
        if cache_key in self._cache and (now - self._cache_time) < _CACHE_TTL:
            self._on_weather(self._cache[cache_key])
            return
        self.desc_label.setText("获取中...")
        self.icon_label.setText("")
        self.temp_label.setText("--")
        self.detail_label.setText("")
        threading.Thread(target=self._do_fetch, args=(city,), daemon=True).start()

    def _do_fetch(self, city: str) -> None:
        try:
            url = f"https://wttr.in/{city}?format=j1&lang=zh"
            resp = self._session.get(url, timeout=15, headers={"User-Agent": "DaFeiYuPet/1.0"})
            resp.raise_for_status()
            data = resp.json()
            current = data.get("current_condition", [{}])[0]
            temp = current.get("temp_C", "--")
            feels = current.get("FeelsLikeC", "--")
            humidity = current.get("humidity", "--")
            wind = current.get("windspeedKmph", "--")
            desc_list = current.get("lang_zh", current.get("weatherDesc", [{}]))
            if isinstance(desc_list, list) and desc_list:
                desc = desc_list[0].get("value", "")
            else:
                desc = ""
            info = {
                "temp": temp, "feels": feels, "humidity": humidity,
                "wind": wind, "desc": desc, "city": city,
                "error": False,
            }
            self._cache[city.lower()] = info
            self._cache_time = time.time()
            self._weather_ready.emit(info)
        except requests.exceptions.Timeout as e:
            log.warning("天气获取失败: %s", e)
            self._weather_ready.emit({"error": True, "msg": "请求超时，请检查网络"})
        except requests.exceptions.ConnectionError as e:
            log.warning("天气获取失败: %s", e)
            self._weather_ready.emit({"error": True, "msg": "连接失败，请检查网络"})
        except requests.exceptions.HTTPError as e:
            log.warning("天气获取失败: %s", e)
            status = e.response.status_code if e.response is not None else "未知"
            self._weather_ready.emit({"error": True, "msg": f"HTTP 错误 {status}"})
        except Exception as e:
            log.warning("天气获取失败: %s", e)
            self._weather_ready.emit({"error": True, "msg": str(e)[:40]})

    def _on_weather(self, info: dict) -> None:
        if info.get("error"):
            self.icon_label.setText("\u2753")
            self.temp_label.setText("--")
            self.desc_label.setText(info.get("msg", "获取失败"))
            self.detail_label.setText("请检查城市名或网络连接")
            return
        desc = info.get("desc", "")
        self.icon_label.setText(_icon_for(desc))
        self.temp_label.setText(f"{info['temp']}\u00b0C")
        cn = _cn_desc(desc)
        self.desc_label.setText(f"{cn}  {self._city}")
        self.detail_label.setText(
            f"体感 {info['feels']}\u00b0C  |  湿度 {info['humidity']}%  |  风速 {info['wind']} km/h"
        )
        parent = self.parent()
        if parent and hasattr(parent, 'notifier'):
            parent.notifier.check_weather_alert(info.get('temp', 0), desc)

    def popup_at(self, x: int, y: int) -> None:
        self.move(x, y)
        self.show()
        self.raise_()
        self.activateWindow()
        if not self.city_edit.text().strip():
            self._fetch()
