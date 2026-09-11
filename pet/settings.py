# -*- coding: utf-8 -*-
"""可视化设置面板：把分散在右键菜单里的开关集中到一个对话框。

覆盖：运动模式 / 大小 / 置顶 / 鼠标穿透 / 开机自启 / 音效。
保存时统一回调 on_apply(new_cfg)，由 PetWindow 负责按字段落地生效。
"""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .config import PetConfig, SIZES
from .styles import THEMES

CJK_FONT = (
    '"Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC",'
    ' "Source Han Sans SC", "Noto Sans CJK SC", sans-serif'
)
CARD_CSS = (
    "QWidget#setCard { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
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
BTN_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 10px; font-size: 14px; font-weight: bold; padding: 8px 0;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
)

MODE_ITEMS = (("自由散步", "wander"), ("跟随鼠标", "follow"), ("原地待着", "still"))
SIZE_ITEMS = tuple(SIZES.items())


class SettingsDialog(QDialog):
    """大肥鱼设置面板。"""

    def __init__(self, cfg: PetConfig, on_apply: Callable[[PetConfig], None], parent=None):
        super().__init__(parent, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("大肥鱼 · 设置")
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self._on_apply = on_apply
        self._build(cfg)
        self.setFixedSize(380, 400)

    def _build(self, cfg: PetConfig) -> None:
        root = QWidget(self)
        root.setObjectName("setCard")
        root.setGeometry(0, 0, 380, 400)
        root.setStyleSheet(CARD_CSS)

        lay = QVBoxLayout(root)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(10)

        title = QLabel("大肥鱼 · 设置")
        title.setStyleSheet(TITLE_CSS)
        lay.addWidget(title)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setSpacing(10)

        self.mode_combo = QComboBox()
        self.mode_combo.setStyleSheet(COMBO_CSS)
        for label, key in MODE_ITEMS:
            self.mode_combo.addItem(label, key)
        idx = next((i for i, (_, k) in enumerate(MODE_ITEMS) if k == cfg.mode), 0)
        self.mode_combo.setCurrentIndex(idx)
        mode_lbl = QLabel("运动模式")
        mode_lbl.setStyleSheet(LABEL_CSS)
        form.addRow(mode_lbl, self.mode_combo)

        self.size_combo = QComboBox()
        self.size_combo.setStyleSheet(COMBO_CSS)
        for label, mult in SIZE_ITEMS:
            self.size_combo.addItem(label, mult)
        sidx = next((i for i, (_, v) in enumerate(SIZE_ITEMS) if abs(v - cfg.size) < 0.01), 1)
        self.size_combo.setCurrentIndex(sidx)
        size_lbl = QLabel("桌宠大小")
        size_lbl.setStyleSheet(LABEL_CSS)
        form.addRow(size_lbl, self.size_combo)

        self.theme_combo = QComboBox()
        self.theme_combo.setStyleSheet(COMBO_CSS)
        for name in THEMES:
            self.theme_combo.addItem(name, name)
        tidx = next((i for i, n in enumerate(THEMES) if n == cfg.theme), 0)
        self.theme_combo.setCurrentIndex(tidx)
        theme_lbl = QLabel("主题皮肤")
        theme_lbl.setStyleSheet(LABEL_CSS)
        form.addRow(theme_lbl, self.theme_combo)

        self.topmost_chk = QCheckBox("窗口置顶（始终在前面）")
        self.topmost_chk.setChecked(cfg.topmost)
        self.topmost_chk.setStyleSheet(CHECK_CSS)
        self.pass_chk = QCheckBox("鼠标穿透（点不到它，只能戳菜单）")
        self.pass_chk.setChecked(cfg.passthrough)
        self.pass_chk.setStyleSheet(CHECK_CSS)
        self.auto_chk = QCheckBox("开机自启")
        self.auto_chk.setChecked(cfg.autostart)
        self.auto_chk.setStyleSheet(CHECK_CSS)
        self.sound_chk = QCheckBox("音效（点击 / 回复轻响）")
        self.sound_chk.setChecked(cfg.sound)
        self.sound_chk.setStyleSheet(CHECK_CSS)
        self.fx_chk = QCheckBox("粒子特效（爱心 / 拖尾 / 扬尘）")
        self.fx_chk.setChecked(cfg.fx_enabled)
        self.fx_chk.setStyleSheet(CHECK_CSS)

        form.addRow(self.topmost_chk)
        form.addRow(self.pass_chk)
        form.addRow(self.auto_chk)
        form.addRow(self.sound_chk)
        form.addRow(self.fx_chk)

        lay.addLayout(form)
        lay.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = QPushButton("取消")
        cancel.setStyleSheet(BTN_CSS)
        cancel.clicked.connect(self.reject)
        save = QPushButton("保存并应用")
        save.setStyleSheet(BTN_CSS)
        save.clicked.connect(self._on_save)
        btn_row.addWidget(cancel, 1)
        btn_row.addWidget(save, 1)
        lay.addLayout(btn_row)

    def _on_save(self) -> None:
        new = PetConfig(
            mode=self.mode_combo.currentData(),
            size=float(self.size_combo.currentData()),
            theme=self.theme_combo.currentData(),
            topmost=self.topmost_chk.isChecked(),
            passthrough=self.pass_chk.isChecked(),
            autostart=self.auto_chk.isChecked(),
            sound=self.sound_chk.isChecked(),
            fx_enabled=self.fx_chk.isChecked(),
            x=None,
            y=None,
        )
        self._on_apply(new)
        self.accept()
