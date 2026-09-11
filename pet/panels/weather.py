# -*- coding: utf-8 -*-
"""天气显示面板：通过 wttr.in 获取天气信息。"""
from __future__ import annotations

import json
import threading

import requests

from ..logger import log
from ..notifications import NotificationManager
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QDialog, QFrame, QGraphicsDropShadowEffect, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QVBoxLayout, QToolButton,
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
TEMP_CSS = (
    "QLabel { color: #f4f2ff; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', monospace; }"
)
DETAIL_CSS = "QLabel { color: #b3aede; font-size: 13px; font-family: " + CJK_FONT + "; }"
DESC_CSS = "QLabel { color: #57e389; font-size: 14px; font-family: " + CJK_FONT + "; }"
HINT_CSS = "QLabel { color: #9a94cf; font-size: 11px; font-family: " + CJK_FONT + "; }"
INPUT_CSS = (
    "QLineEdit { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "padding: 6px 10px; font-size: 13px; font-family: " + CJK_FONT + "; }"
    "QLineEdit:focus { border: 1px solid rgba(140,128,255,0.8); }"
)
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 13px; font-weight: bold; padding: 8px 16px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
)
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
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


class WeatherPanel(QDialog):
    """天气显示面板。"""
    _weather_ready = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("天气")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._weather_ready.connect(self._on_weather)

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
        lay.setSpacing(6)

        # 标题行（含关闭按钮）
        head = QHBoxLayout()
        title = QLabel("天气")
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

        city_row = QHBoxLayout()
        city_row.setSpacing(6)
        self.city_edit = QLineEdit()
        self.city_edit.setPlaceholderText("城市名 (如 Beijing / 上海)")
        self.city_edit.setStyleSheet(INPUT_CSS)
        self.city_edit.returnPressed.connect(self._fetch)
        city_row.addWidget(self.city_edit, 1)
        fetch_btn = QPushButton("查询")
        fetch_btn.setStyleSheet(BTN_CSS)
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
        self._session = requests.Session()
        self.hide()

    def _fetch(self) -> None:
        city = self.city_edit.text().strip() or "Beijing"
        self._city = city
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
            # 优先中文描述，回退英文
            desc_list = current.get("lang_zh", current.get("weatherDesc", [{}]))
            if isinstance(desc_list, list) and desc_list:
                desc = desc_list[0].get("value", "")
            else:
                desc = ""
            self._weather_ready.emit({
                "temp": temp, "feels": feels, "humidity": humidity,
                "wind": wind, "desc": desc, "city": city,
                "error": False,
            })
        except requests.exceptions.Timeout as e:
            log.warning("天气获取失败: %s", e)
            self._weather_ready.emit({"error": True, "msg": "请求超时，请检查网络"})
        except requests.exceptions.ConnectionError as e:
            log.warning("天气获取失败: %s", e)
            self._weather_ready.emit({"error": True, "msg": "连接失败，请检查网络"})
        except requests.exceptions.HTTPError as e:
            log.warning("天气获取失败: %s", e)
            self._weather_ready.emit({"error": True, "msg": f"HTTP 错误 {e.response.status_code}"})
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
        # 触发天气通知
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
