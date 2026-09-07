# -*- coding: utf-8 -*-
"""桌宠交互面板：「鲸语讯道」AI 对话面板（双击桌宠或右键菜单打开）。

设计理念（区别于旧版单行输入框聊天）：
- 深色"深海讯道"玻璃卡片：磨砂深蓝紫底 + 霓虹描边 + 投影，随鲸鱼娘世界观；
- 头部：🐳 头像 + 「鲸语讯道 · 大肥鱼在线」状态点 + 一键收起；
- 消息流：双色对话气泡（用户=右侧蓝紫发光，大肥鱼=左侧白玻璃），自动滚动到底；
- 回话期间显示「正在码字…」动态点动画；输入框回车即发；
- 首屏：有持久化历史则回放，否则显示一句开场白（均在 pet_window 中决定）。
"""
from __future__ import annotations

from typing import Callable, List, Optional

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# 主题常量
# CJK 友好字体：优先微软雅黑 UI（Windows 上中文最清晰锐利的 UI 字体），
# 依次回退到雅黑 / 苹方 / 思源黑体，避免回退到细体衬线导致中文发虚。
CJK_FONT = (
    '"Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC",'
    ' "Source Han Sans SC", "Noto Sans CJK SC", sans-serif'
)
CARD_CSS = (
    "QFrame#chatCard { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 rgba(38,36,66,0.96), stop:1 rgba(24,22,48,0.96));"
    "border: 1px solid rgba(148,130,255,0.35); border-radius: 18px;"
    "font-family: " + CJK_FONT + "; }"
)
TITLE_CSS = (
    "QLabel { color: #f4f2ff; font-size: 15px; font-weight: 600;"
    "font-family: " + CJK_FONT + "; }"
)
SUB_CSS = (
    "QLabel { color: #b3aede; font-size: 11px; letter-spacing: 0.3px;"
    "font-family: " + CJK_FONT + "; }"
)
USER_BUBBLE_CSS = (
    "QLabel { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: #ffffff; border-radius: 14px;"
    "padding: 9px 13px; font-size: 14px; font-weight: 500;"
    "letter-spacing: 0.2px; font-family: " + CJK_FONT + "; }"
)
PET_BUBBLE_CSS = (
    # 实色中紫气泡 + 纯白文字 + 微软雅黑 medium 字重：
    # 在深紫卡片（~#262442）上气泡明显成块、纯白文字极清晰
    "QLabel { background: #2e2c4d; color: #ffffff;"
    "border: 1px solid rgba(148,130,255,0.40); border-radius: 14px;"
    "padding: 9px 13px; font-size: 14px; font-weight: 500;"
    "letter-spacing: 0.2px; line-height: 1.45; font-family: " + CJK_FONT + "; }"
)
ERR_BUBBLE_CSS = (
    # 与 PET_BUBBLE_CSS 统一基底（实色中紫 + 纯白 + 微软雅黑 medium），
    # 仅把描边换成红色以保留"这是错误"的语义
    "QLabel { background: #2e2c4d; color: #ffffff;"
    "border: 1px solid rgba(255,120,120,0.55); border-radius: 14px;"
    "padding: 9px 13px; font-size: 14px; font-weight: 500;"
    "letter-spacing: 0.2px; line-height: 1.45; font-family: " + CJK_FONT + "; }"
)
INPUT_CSS = (
    "QLineEdit { background: rgba(255,255,255,0.10); color: #f3f1ff;"
    "border: 1px solid rgba(255,255,255,0.18); border-radius: 16px;"
    "padding: 8px 14px; font-size: 14px; font-family: " + CJK_FONT + "; }"
    "QLineEdit:focus { border: 1px solid rgba(140,128,255,0.8); }"
)
SEND_CSS = (
    "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
    "stop:0 #6f6cff, stop:1 #4f8bff); color: white; border: none;"
    "border-radius: 17px; font-size: 16px; font-weight: bold;"
    "font-family: " + CJK_FONT + "; }"
    "QPushButton:hover { background: #7d7aff; }"
    "QPushButton:disabled { background: rgba(120,120,160,0.5); }"
)
CLOSE_CSS = (
    "QToolButton { color: #9a94cf; border: none; border-radius: 12px;"
    "font-size: 15px; background: transparent; font-family: " + CJK_FONT + "; }"
    "QToolButton:hover { background: rgba(255,90,110,0.25); color: #ffb9c4; }"
)
SCROLL_CSS = "QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 0; }"
DOT_CSS = (
    "QLabel { color: #b0a8df; font-size: 13px; padding: 2px 4px;"
    "font-family: " + CJK_FONT + "; }"
)


class DeepChatPanel(QDialog):
    """鲸语讯道：新颖形态的 AI 对话面板。"""

    def __init__(self, on_send: Callable[[str], None], parent=None):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint,
        )
        self._on_send = on_send
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # 基线 CJK 字体：作为兜底，确保所有未单独设置样式的文本控件
        # 也能使用清晰的中文 UI 字体（微软雅黑 UI）。
        self.setFont(QFont("Microsoft YaHei UI", 11))
        self.setFixedSize(330, 430)

        # 卡片容器（带阴影与渐变描边）
        card = QFrame(self)
        card.setObjectName("chatCard")
        card.setGeometry(0, 0, 330, 430)
        card.setStyleSheet(CARD_CSS)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(10, 6, 60, 170))
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(8)

        # ---- 头部：头像 + 标题 + 在线点 + 收起 ----
        head = QHBoxLayout()
        head.setSpacing(8)
        avatar = QLabel("🐳")
        avatar.setFont(QFont("Segoe UI Emoji", 20))
        head.addWidget(avatar)
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        title = QLabel("鲸语讯道")
        title.setStyleSheet(TITLE_CSS)
        sub = QLabel("大肥鱼在线 · DeepSeek 已接通")
        sub.setStyleSheet(SUB_CSS)
        title_box.addWidget(title)
        title_box.addWidget(sub)
        head.addLayout(title_box)
        head.addStretch(1)
        self._dot = QLabel("●")
        self._dot.setStyleSheet("color: #57e389; font-size: 11px;")
        head.addWidget(self._dot)
        close_btn = QToolButton()
        close_btn.setText("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet(CLOSE_CSS)
        close_btn.clicked.connect(self.hide)
        head.addWidget(close_btn)
        lay.addLayout(head)

        # ---- 消息流 ----
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet(SCROLL_CSS)
        body = QWidget()
        self._flow = QVBoxLayout(body)
        self._flow.setContentsMargins(0, 2, 0, 2)
        self._flow.setSpacing(8)
        self._flow.addStretch(1)  # 保持内容靠上、新消息贴底
        self._scroll.setWidget(body)
        lay.addWidget(self._scroll)

        # 开场白 / 历史回放由 pet_window 在构建后决定（见 _build_panels）

        # ---- 打字指示（动态点动画）----
        self._typing = QLabel("")
        self._typing.setStyleSheet(DOT_CSS)
        self._typing.hide()
        self._flow.insertWidget(self._flow.count() - 1, self._typing)

        self._dot_timer = QTimer(self)
        self._dot_timer.setInterval(420)
        self._dot_timer.timeout.connect(self._tick_dot)

        # ---- 输入行 ----
        row = QHBoxLayout()
        row.setSpacing(8)
        self.input = QLineEdit()
        self.input.setPlaceholderText("给大肥鱼发消息…（Enter 发送）")
        self.input.setStyleSheet(INPUT_CSS)
        self.input.returnPressed.connect(self._send)
        row.addWidget(self.input, 1)
        send_btn = QPushButton("➤")
        send_btn.setFixedSize(34, 34)
        send_btn.setStyleSheet(SEND_CSS)
        send_btn.clicked.connect(self._send)
        row.addWidget(send_btn)
        lay.addLayout(row)

        self.hide()

    # ---------- 对外接口 ----------
    def popup_at(self, x: int, y: int) -> None:
        self.move(int(x), int(y))
        self.show()
        self.raise_()
        self.activateWindow()
        self.input.setFocus()
        self._fade(0.0, 1.0, 180)

    def show_greeting(self) -> None:
        """首屏尚未有历史时，显示一句开场白。"""
        self.add_message("assistant", "主人好，我是大肥鱼🐳 今天想聊点什么？")

    def load_history(self, messages: List[dict]) -> None:
        """把持久化历史回放成气泡（重启后恢复对话上下文）。"""
        for d in messages:
            role = d.get("role")
            text = d.get("content", "")
            if role in ("user", "assistant", "err") and text:
                self.add_message(role, text)

    def add_message(self, role: str, text: str) -> None:
        """追加一条消息气泡：user 右侧蓝紫；assistant/err 左侧玻璃。"""
        text = (text or "").strip()
        if not text:
            return
        # 错误消息统一加 ⚠ 前缀，与普通助手消息在内容层也做区分
        if role == "err":
            text = "⚠ " + text
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(238)
        bubble.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if role == "user":
            bubble.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bubble.setStyleSheet(USER_BUBBLE_CSS)
            align, stretch_before, stretch_after = Qt.AlignmentFlag.AlignRight, True, False
        elif role == "err":
            bubble.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bubble.setStyleSheet(ERR_BUBBLE_CSS)
            align, stretch_before, stretch_after = Qt.AlignmentFlag.AlignLeft, False, True
        else:
            bubble.setAlignment(Qt.AlignmentFlag.AlignLeft)
            bubble.setStyleSheet(PET_BUBBLE_CSS)
            align, stretch_before, stretch_after = Qt.AlignmentFlag.AlignLeft, False, True
        row = QWidget()
        row_lay = QHBoxLayout(row)
        row_lay.setContentsMargins(0, 0, 0, 0)
        row_lay.setSpacing(0)
        if stretch_before:
            row_lay.addStretch(1)
        row_lay.addWidget(bubble)
        if stretch_after:
            row_lay.addStretch(1)
        self._flow.insertWidget(self._flow.count() - 1, row)
        self._scroll_to_bottom()

    def set_typing(self, on: bool) -> None:
        """显示/隐藏「正在码字…」动态指示。"""
        if on:
            self._typing.setText("大肥鱼正在码字")
            self._typing.show()
            self._dot_timer.start()
        else:
            self._typing.hide()
            self._dot_timer.stop()
        self._scroll_to_bottom()

    # ---------- 内部 ----------
    def _tick_dot(self) -> None:
        n = (self._typing.text().count("·") % 3) + 1
        self._typing.setText("大肥鱼正在码字" + "·" * n)
        self._scroll_to_bottom()

    def _send(self) -> None:
        text = self.input.text().strip()
        if not text:
            return
        self.input.clear()
        self._on_send(text)

    def _scroll_to_bottom(self) -> None:
        bar = self._scroll.verticalScrollBar()
        QTimer.singleShot(0, lambda: bar.setValue(bar.maximum()))

    def _fade(self, start: float, end: float, ms: int) -> None:
        anim = QPropertyAnimation(self, b"windowOpacity", self)
        anim.setDuration(ms)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        self._fade_anim = anim  # 防止被回收

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)
