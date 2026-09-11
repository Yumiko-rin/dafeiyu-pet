# -*- coding: utf-8 -*-
"""公共样式模块：所有面板共享的 CSS 常量，消除重复定义。"""
from __future__ import annotations

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

TITLE_CSS = (
    "QLabel { color: #f4f2ff; font-size: 15px; font-weight: 600;"
    "font-family: " + CJK_FONT + "; }"
)

LABEL_CSS = (
    "QLabel { color: #cfc9f2; font-size: 13px; font-family: " + CJK_FONT + "; }"
)

HINT_CSS = (
    "QLabel { color: #9a94cf; font-size: 11px; font-family: " + CJK_FONT + "; }"
)

CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 14px;"
    "font-size: 16px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.30); color: #ffb9c4; }"
)

BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 14px; font-weight: bold; padding: 8px 16px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
    "QPushButton:disabled { background: rgba(120,120,160,0.5); }"
)

BTN_RESET_CSS = (
    "QPushButton { background: rgba(255,255,255,0.12); color: #cfc9f2;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "font-size: 14px; font-weight: bold; padding: 8px 16px;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: rgba(255,255,255,0.20); }"
)

INPUT_CSS = (
    "QLineEdit { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "padding: 6px 10px; font-size: 13px; font-family: " + CJK_FONT + "; }"
    "QLineEdit:focus { border: 1px solid rgba(140,128,255,0.8); }"
)

SPIN_CSS = (
    "QSpinBox { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 8px;"
    "padding: 4px; font-size: 14px; font-family: " + CJK_FONT + "; }"
    "QSpinBox::up-button, QSpinBox::down-button { width: 20px; }"
)

CHECK_CSS = (
    "QCheckBox { color: #cfc9f2; font-size: 13px; spacing: 6px;"
    "font-family: " + CJK_FONT + "; }"
    "QCheckBox::indicator { width: 16px; height: 16px;"
    "border-radius: 4px; border: 1px solid rgba(148,130,255,0.6);"
    "background: rgba(255,255,255,0.08); }"
    "QCheckBox::indicator:checked { background: #6f6cff;"
    "image: none; border: 1px solid #8f8cff; }"
)

COMBO_CSS = (
    "QComboBox { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 10px;"
    "padding: 5px 8px; font-size: 13px; font-family: " + CJK_FONT + "; }"
    "QComboBox QAbstractItemView { background: #2a2848; color: #f3f1ff;"
    "selection-background-color: #6f6cff; font-family: " + CJK_FONT + "; }"
)

DISPLAY_CSS = (
    "QLabel { color: #57e389; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', 'Courier New', monospace; }"
)

DISPLAY_REST_CSS = (
    "QLabel { color: #ffb86c; font-size: 48px; font-weight: 700;"
    "font-family: 'Consolas', 'Courier New', monospace; }"
)

STAT_CSS = (
    "QLabel { color: #f4f2ff; font-size: 14px; font-weight: 600;"
    "font-family: " + CJK_FONT + "; }"
)

VALUE_CSS = (
    "QLabel { color: #f4f2ff; font-size: 13px; font-weight: 600;"
    "font-family: " + CJK_FONT + "; }"
)

# ---- 主题配色 ----
THEMES = {
    "默认紫": {
        "accent": (111, 108, 255),
        "glow": (140, 128, 255),
        "bar_cpu": (111, 108, 255),
        "bar_mem": (79, 139, 255),
        "bar_dsk": (87, 227, 137),
    },
    "薄荷绿": {
        "accent": (87, 227, 137),
        "glow": (87, 227, 137),
        "bar_cpu": (87, 227, 137),
        "bar_mem": (79, 199, 255),
        "bar_dsk": (255, 184, 108),
    },
    "樱花粉": {
        "accent": (255, 120, 180),
        "glow": (255, 120, 180),
        "bar_cpu": (255, 120, 180),
        "bar_mem": (255, 160, 130),
        "bar_dsk": (180, 130, 255),
    },
    "深海蓝": {
        "accent": (79, 139, 255),
        "glow": (79, 139, 255),
        "bar_cpu": (79, 139, 255),
        "bar_mem": (111, 108, 255),
        "bar_dsk": (87, 227, 137),
    },
}
