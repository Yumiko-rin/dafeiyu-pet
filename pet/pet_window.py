# -*- coding: utf-8 -*-
"""大肥鱼桌宠主窗口：三视图透明桌宠 + 动画 + 交互 + 托盘。

- 左键按住：拖拽（侧身朝向拖动方向）
- 单击：蹦跳 + 回嘴（轻响）
- 双击 / 右键菜单：打开「鲸语讯道」AI 对话面板
- 右键 / 托盘：完整菜单（含可视化设置面板）
- AI 对话与余额查询均在后台线程执行，主线程永不阻塞
- 摸鱼氛围：空闲时随机戳一戳 / 自发碎碎念
"""
from __future__ import annotations

import ctypes
import math
import os
import random
import subprocess
import sys
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QTimer, QPoint, QPointF, QRectF
from PySide6.QtGui import (
    QPainter,
    QPixmap,
    QFont,
    QColor,
    QIcon,
    QFontMetrics,
    QPolygonF,
    QLinearGradient,
    QBrush,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QMenu,
    QSystemTrayIcon,
    QMessageBox,
    QInputDialog,
    QLineEdit,
)

from . import APP_NAME, __version__
from .config import (
    PetConfig,
    SIZES,
    SPRITE_BASE_H,
    app_dir,
    default_config_path,
    load_config,
    save_config,
    sprite_dir,
    sprite_height,
)
from .lines import LINES, REACT_LINES, INNER_LINES, DRAG_LINES, MUTTER_LINES, POKE_LINES
from .panels import DeepChatPanel
from .services import PetServices
from .sound import SoundManager
from .settings import SettingsDialog

BUBBLE_H = 56
BUBBLE_DUR = 2.8        # 气泡停留时长（秒）
BUBBLE_FADE_IN = 0.16   # 出现淡入时长（秒）
BUBBLE_FADE_OUT = 0.22  # 消失淡出时长（秒）
MARGIN = 4
SPEED = 380.0
TICK = 20


class PetWindow(QWidget):
    """透明桌宠窗口。"""

    def __init__(self):
        self.cfg: PetConfig = load_config(default_config_path())
        self.services = PetServices(
            api_key=self.cfg.api_key,
            api_base=self.cfg.api_base,
            model=self.cfg.model,
        )
        self.sound = SoundManager(enabled=self.cfg.sound)

        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.cfg.topmost:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(APP_NAME)

        self._load_sprites()
        self._init_state()
        self._build_panels()
        self._build_tray()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(TICK)

        x, y = self.cfg.x, self.cfg.y
        if x is None or y is None:
            screen = QApplication.primaryScreen().availableGeometry()
            x = screen.right() - self.width() - 80
            y = screen.bottom() - self.height() - 60
        self.move(int(x), int(y))
        self.show()
        self.snap_into_screen()
        if self.cfg.passthrough:
            self._apply_passthrough(True)

    # ---------- 初始化 ----------
    def _load_sprites(self) -> None:
        self.sprites = {}
        for mult in SIZES.values():
            h = sprite_height(mult)
            for name in ("正面", "侧面", "背面"):
                sized = os.path.join(sprite_dir(), f"{name}_{h}.png")
                if os.path.exists(sized):
                    pix = QPixmap(sized)
                else:
                    pix = QPixmap(os.path.join(sprite_dir(), f"{name}.png")).scaledToHeight(
                        h, Qt.TransformationMode.SmoothTransformation
                    )
                self.sprites[(name, h)] = pix
        self.icon = QIcon(os.path.join(sprite_dir(), "icon.png"))

    def _init_state(self) -> None:
        self.cur_h = sprite_height(self.cfg.size)
        self.win_mx = int(self.cur_h * 0.062) + 6
        self.win_w = max(
            p.width() for k, p in self.sprites.items() if k[1] == self.cur_h
        ) + self.win_mx * 2
        self.setFixedSize(self.win_w, self.cur_h + BUBBLE_H + MARGIN * 2 + 10)

        self.mode = self.cfg.mode
        self.dir = "down"
        self.facing = 1
        self.target: Optional[Tuple[int, int]] = None
        self.rest_until = 0
        self.cur_speed = 0.0
        self.prev_key = None
        self.cross_t = 0.0
        self.action = None
        self.action_t = 0.0
        self.bubble_text = ""
        self.bubble_until = 0.0
        self.bubble_in_at = 0.0
        self.bubble_inner = False
        self.last_speak_tick = 0
        self.t = 0
        self.jump_t = 0.0
        self.dragging = False
        self.drag_offset = None
        self.drag_start_pos = None
        self.last_line = ""
        self.bubble_font = QFont("Microsoft YaHei UI", 11)

    def _build_panels(self) -> None:
        self.chat_panel = DeepChatPanel(self.submit_chat, self)

        # 首屏：有持久化历史则回放，否则一句开场白
        hist = self.services.get_history()
        if hist:
            self.chat_panel.load_history(hist)
        else:
            self.chat_panel.show_greeting()

        # 单击延迟判定（区分单击/双击）
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_single_click)

        # 摸鱼氛围：随机戳一戳 / 自发碎碎念
        self._ambient_timer = QTimer(self)
        self._ambient_timer.setInterval(90000)
        self._ambient_timer.timeout.connect(self._ambient_tick)
        self._ambient_timer.start()

    def _build_tray(self) -> None:
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self.icon, self)
        self.tray.setContextMenu(self._build_menu())
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    # ---------- 对话 / 余额 ----------
    def submit_chat(self, text: str) -> None:
        """面板发送消息：无 Key 提示；忙碌时暂缓；否则入队请求。"""
        if not self.cfg.api_key:
            self.chat_panel.set_typing(False)
            self.chat_panel.add_message("err", "还没配 Key：右键菜单「设置」里填好就能开聊啦～")
            return
        if self.services.is_busy():
            self.chat_panel.add_message("err", "我上一句还没码完，等我一下下！")
            return
        self.chat_panel.add_message("user", text)
        self.chat_panel.set_typing(True)
        self.services.ask(text)

    def _chat_position(self):
        """计算对话框应出现的坐标：桌宠头顶、水平居中。"""
        pw, ph = self.chat_panel.width(), self.chat_panel.height()
        geo = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        cx = self.x() + self.width() // 2
        x = int(cx - pw / 2)
        # 头顶上方留 12px；放不下则翻到脚下
        y = int(self.y() - ph - 12)
        if y < geo.top():
            y = int(self.y() + self.height() + 12)
        # 水平夹在屏内
        x = max(geo.left(), min(geo.right() - pw, x))
        # 极端：脚下也放不下 → 顶部兜底
        if y + ph > geo.bottom():
            y = geo.top()
        return x, y

    def _sync_chat(self) -> None:
        """对话面板可见时，把它吸到桌宠头顶（跟随拖动 / 行走）。"""
        if self.chat_panel.isVisible():
            x, y = self._chat_position()
            self.chat_panel.move(x, y)

    def open_chat(self) -> None:
        """打开鲸语讯道（浮在桌宠头顶、水平居中）。"""
        self.target = None  # 对话打开时原地待命，不让它乱跑
        self.sound.play("pop")
        x, y = self._chat_position()
        self.chat_panel.popup_at(x, y)

    def _get_balance(self) -> None:
        self.services.fetch_balance()

    # ---------- 绘制 ----------
    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        now = self.t * TICK / 1000.0

        if self.bubble_text:
            # 淡入 / 淡出透明度：出现后 FADE_IN 内淡入，bubble_until 后 FADE_OUT 内淡出
            now_in = (now - self.bubble_in_at) / BUBBLE_FADE_IN
            in_a = max(0.0, min(1.0, now_in)) if now_in >= 0.0 else 0.0
            if now < self.bubble_until:
                out_a = 1.0
            else:
                out_a = max(0.0, (self.bubble_until + BUBBLE_FADE_OUT - now) / BUBBLE_FADE_OUT)
            alpha = in_a * out_a
            if alpha > 0.004 and now < self.bubble_until + BUBBLE_FADE_OUT:
                bfont = QFont(self.bubble_font)
                # 配色分层：normal=白玻璃+紫描边；inner=深色玻璃+金色强调条
                if self.bubble_inner:
                    bfont.setItalic(True)
                    radius, accent = 16.0, True
                    top_c, bot_c, tail_c = QColor(72, 70, 112), QColor(40, 40, 66), QColor(48, 47, 76)
                    fg, border_c = QColor(238, 238, 250), QColor(170, 150, 255, 120)
                else:
                    radius, accent = 14.0, False
                    top_c, bot_c, tail_c = QColor(255, 255, 255), QColor(245, 246, 254), QColor(249, 250, 255)
                    fg, border_c = QColor(46, 46, 77), QColor(150, 125, 255, 70)
                fm = QFontMetrics(bfont)
                max_w = min(240, self.width() - 16)
                lines = []
                cur = ""
                for ch in self.bubble_text:
                    if fm.horizontalAdvance(cur + ch) > max_w - 20:
                        lines.append(cur)
                        cur = ch
                    else:
                        cur += ch
                lines.append(cur)
                # 心声态左侧让出强调条空间
                lead = 14 if accent else 0
                text_w = max(fm.horizontalAdvance(l) for l in lines)
                bw = text_w + 20 + lead
                bh = len(lines) * fm.height() + 14
                bx = (self.width() - bw) / 2
                by = 6.0
                rect = QRectF(bx, by, bw, bh)

                p.save()
                p.setOpacity(alpha)
                p.setPen(Qt.PenStyle.NoPen)
                # 柔和分层投影（三层错位，越靠下越浅）
                for i, dy in enumerate((3.4, 2.1, 1.0)):
                    p.setBrush(QColor(24, 18, 70, max(4, 30 - i * 11)))
                    p.drawRoundedRect(QRectF(bx, by + dy, bw, bh), radius, radius)
                # 主体：纵向渐变 + 半透明描边
                grad = QLinearGradient(0, by, 0, by + bh)
                grad.setColorAt(0.0, top_c)
                grad.setColorAt(1.0, bot_c)
                p.setBrush(QBrush(grad))
                p.setPen(QColor(border_c.red(), border_c.green(), border_c.blue(), int(border_c.alpha() * alpha)))
                p.drawRoundedRect(rect, radius, radius)
                # 尾巴（底边三角，与底色尾端衔接）
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(tail_c)
                tail = QPointF(self.width() / 2, by + bh)
                p.drawPolygon(
                    QPolygonF(
                        [tail, QPointF(tail.x() - 7, tail.y() + 9), QPointF(tail.x() + 7, tail.y() + 9)]
                    )
                )
                # 心声态：左侧金色强调条（关键状态突出）
                if accent:
                    p.setBrush(QColor(255, 205, 120, 235))
                    p.drawRoundedRect(QRectF(bx + 6, by + 8, 3, bh - 16), 1.5, 1.5)
                # 文字（inner 斜体，视觉左移以避开强调条）
                p.setPen(fg)
                p.setFont(bfont)
                tx0 = bx + lead / 2
                tw = text_w + 20
                for i, line in enumerate(lines):
                    p.drawText(
                        QRectF(tx0, by + 7 + i * fm.height(), tw, fm.height()),
                        Qt.AlignmentFlag.AlignCenter,
                        line,
                    )
                p.restore()

        cx = self.width() / 2
        walking = self.target is not None and not self.dragging
        if walking:
            sway = math.sin(now * 9.0) * 3.5
            bob = -abs(math.sin(now * 4.5)) * 7.0
        else:
            sway = math.sin(now * 2.5) * 1.5
            bob = 0.0
        breath = 1.0 + 0.02 * math.sin(now * 2.5)
        scale = breath
        jump = -abs(math.sin(self.jump_t * 3.14159)) * 14 * self.jump_t if self.jump_t > 0 else 0
        act_rot = act_sx = act_sy = 0.0
        if self.action == "sway":
            act_rot = math.sin(self.action_t * 3.14159 * 2) * 10 * self.action_t
        elif self.action == "stretch":
            act_sy = 0.06 * math.sin(self.action_t * 3.14159)
            act_sx = -0.03 * math.sin(self.action_t * 3.14159)

        def draw_one(key, opacity):
            if key is None:
                return
            name, h, facing = key
            pix = self.sprites[(name, h)]
            ph = pix.height() * scale * (1 + act_sy)
            pw = pix.width() * scale * (1 + act_sx)
            dx = cx - pw / 2
            bottom = BUBBLE_H + MARGIN + self.cur_h
            dy = bottom - ph + jump + bob
            p.save()
            p.setOpacity(opacity)
            p.translate(cx, bottom)
            p.rotate(sway + act_rot)
            p.translate(-cx, -bottom)
            if facing < 0:
                p.translate(cx, 0)
                p.scale(-1, 1)
                p.translate(-cx, 0)
            p.drawPixmap(QRectF(dx, dy, pw, ph), pix, QRectF(0, 0, pix.width(), pix.height()))
            p.restore()

        cur_key = self._sprite_key()
        if self.cross_t > 0:
            draw_one(self.prev_key, self.cross_t)
            draw_one(cur_key, 1.0 - self.cross_t)
        else:
            draw_one(cur_key, 1.0)

    def _sprite_key(self):
        name = {"left": "侧面", "right": "侧面", "up": "背面", "down": "正面"}[self.dir]
        return (name, self.cur_h, self.facing if self.dir in ("left", "right") else 1)

    def _set_dir(self, d: str, facing: Optional[int] = None) -> None:
        if d != self.dir:
            self.prev_key = self._sprite_key()
            self.cross_t = 1.0
            self.dir = d
        if facing is not None and facing != self.facing:
            self.facing = facing

    # ---------- 逻辑 ----------
    def tick(self) -> None:
        self.t += 1

        # 消费后台线程消息（线程安全）
        for msg in self.services.drain_messages():
            if msg[0] == "say":
                self.say(msg[1])
            elif msg[0] == "chat":
                self.chat_panel.set_typing(False)
                self.chat_panel.add_message(msg[1], msg[2])
                if msg[1] == "assistant":
                    self.sound.play("ding")  # 收到回复来一声轻响

        if self.jump_t > 0:
            self.jump_t = max(0.0, self.jump_t - 0.06)
        if self.cross_t > 0:
            self.cross_t = max(0.0, self.cross_t - 0.15)
        if self.action_t > 0:
            self.action_t = max(0.0, self.action_t - 0.03)
            if self.action_t == 0:
                self.action = None

        if self.dragging:
            self.update()
            return

        # 对话面板打开时原地待命：不再游走 / 触发待机动作，气泡只在头顶对话框
        chat_open = self.chat_panel.isVisible()
        if chat_open:
            self.target = None
            self.update()
            return

        now_ms = self.t * TICK

        if self.mode == "follow":
            cursor = self.cursor().pos()
            screen = QApplication.screenAt(cursor) or self.screen() or QApplication.primaryScreen()
            geo = screen.availableGeometry()
            near = (
                self.x() - 100 <= cursor.x() <= self.x() + self.width() + 100
                and self.y() - 100 <= cursor.y() <= self.y() + self.height() + 100
            )
            if near:
                self.target = None
            else:
                tx = max(geo.left(), min(geo.right() - self.width(), cursor.x() - self.width() / 2))
                ty = max(geo.top(), min(geo.bottom() - self.height(), cursor.y() - 90))
                self.target = (tx, ty)
        elif self.mode == "wander":
            if self.target is None:
                if now_ms < self.rest_until:
                    self._maybe_idle_action()
                    self.update()
                    return
                geo = (self.screen() or QApplication.primaryScreen()).availableGeometry()
                self.target = (
                    random.randint(geo.left() + 40, geo.right() - self.width() - 40),
                    random.randint(geo.top() + 40, geo.bottom() - self.height() - 40),
                )
        else:  # still
            self._maybe_idle_action()
            self.update()
            return

        if self.target is not None:
            cx, cy = self.x() + self.width() / 2, self.y() + self.height() / 2
            dx, dy = self.target[0] - cx, self.target[1] - cy
            dist = (dx * dx + dy * dy) ** 0.5
            if dist < 12:
                self.target = None
                self.rest_until = self.t * TICK + random.randint(8000, 18000)
                self._set_dir("down")
            else:
                step = self.cur_speed * TICK / 1000.0
                nx, ny = cx + dx / dist * step, cy + dy / dist * step
                self.move(int(nx - self.width() / 2), int(ny - self.height() / 2))
                self._sync_chat()
                if abs(dx) > abs(dy) * 1.15:
                    self._set_dir("left" if dx < 0 else "right", 1 if dx < 0 else -1)
                else:
                    self._set_dir("up" if dy < 0 else "down")
            if random.random() < 0.002 and self.jump_t == 0:
                self.jump_t = 0.5

        target_speed = SPEED if self.target is not None else 0.0
        self.cur_speed += (target_speed - self.cur_speed) * 0.3
        self.update()

    def _maybe_idle_action(self) -> None:
        if random.random() < 0.01:
            pick = random.random()
            if pick < 0.35:
                self.jump_t = 1.0
            elif pick < 0.6:
                self.action, self.action_t = "sway", 1.0
            elif pick < 0.8:
                self.action, self.action_t = "stretch", 1.0
            elif pick < 0.9:
                if self.t - self.last_speak_tick >= 1500:
                    self.last_speak_tick = self.t
                    if pick < 0.82:
                        self.say(random.choice(INNER_LINES), inner=True)
                    else:
                        self.say(random.choice(LINES))

    def _ambient_tick(self) -> None:
        """摸鱼氛围：空闲时随机戳一戳或自发碎碎念，增强陪伴感。"""
        if self.chat_panel.isVisible() or self.dragging:
            return
        if random.random() < 0.5:
            self.say(random.choice(POKE_LINES))
            self.sound.play("pop")
        else:
            self.say(random.choice(MUTTER_LINES))

    def say(self, text: str, inner: bool = False) -> None:
        now = self.t * TICK / 1000.0
        if text == self.last_line and now < self.bubble_until:
            return  # 同句且仍在展示中才跳过；过期后可重新说
        self.last_line = text
        self.bubble_inner = inner
        self.bubble_text = f"（{text}）" if inner else text
        self.bubble_in_at = now
        self.bubble_until = now + BUBBLE_DUR
        self.update()

    # ---------- 鼠标事件 ----------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint()
            self.dragging = False

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_start_pos is not None:
            delta = event.globalPosition().toPoint() - self.drag_start_pos
            if not self.dragging and delta.manhattanLength() > 6:
                self.dragging = True
                self.drag_offset = event.globalPosition().toPoint() - QPoint(self.x(), self.y())
            if self.dragging and self.drag_offset is not None:
                pos = event.globalPosition().toPoint() - self.drag_offset
                self.move(pos)
                self._sync_chat()
                if abs(delta.x()) > 10:
                    self._set_dir("left" if delta.x() < 0 else "right", 1 if delta.x() < 0 else -1)
                self.update()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                self.dragging = False
                self.drag_offset = None
                self.drag_start_pos = None
                self._set_dir("down", 1)
                self.target = None
                self.rest_until = self.t * TICK + random.randint(6000, 14000)
                if random.random() < 0.5:
                    self.say(random.choice(DRAG_LINES))
            else:
                self._click_timer.start(280)
            self.drag_start_pos = None

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            self._click_timer.stop()
            self.open_chat()

    def _on_single_click(self) -> None:
        if random.random() < 0.7:
            self.jump_t = 1.0
            self.sound.play("pop")  # 点击蹦跳来一声轻响
        if random.random() < 0.6:
            self.say(random.choice(REACT_LINES))

    def contextMenuEvent(self, event) -> None:  # noqa: N802
        self._build_menu().exec(event.globalPos())

    # ---------- 菜单 ----------
    def _build_menu(self) -> QMenu:
        m = QMenu(self)
        mode_menu = m.addMenu("模式")
        for label, key in (("自由散步", "wander"), ("跟随鼠标", "follow"), ("原地待着", "still")):
            a = mode_menu.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.mode == key)
            a.triggered.connect(lambda _=False, k=key: self.set_mode(k))

        size_menu = m.addMenu("大小")
        for label, mult in SIZES.items():
            a = size_menu.addAction(label)
            a.setCheckable(True)
            a.setChecked(abs(self.cur_h - SPRITE_BASE_H * mult) < 2)
            a.triggered.connect(lambda _=False, v=mult: self.set_size(v))

        m.addAction("AI 对话（双击我）", self.open_chat)
        m.addAction("设置…", self._open_settings)
        m.addAction("查看模型余额", self._get_balance)
        m.addSeparator()
        m.addAction("显示/隐藏", self.toggle_visible)
        m.addAction("回到屏幕内", self.snap_into_screen)
        pa = m.addAction("鼠标穿透（点不到它）")
        pa.setCheckable(True)
        pa.setChecked(self.cfg.passthrough)
        pa.triggered.connect(self.set_passthrough)
        ta = m.addAction("窗口置顶")
        ta.setCheckable(True)
        ta.setChecked(self.cfg.topmost)
        ta.triggered.connect(self.set_topmost)
        aa = m.addAction("开机自启")
        aa.setCheckable(True)
        aa.setChecked(self.cfg.autostart)
        aa.triggered.connect(self.set_autostart)
        m.addSeparator()
        m.addAction("退出", self.quit_app)
        return m

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self.cfg, self._apply_settings, self)
        dlg.exec()

    def _apply_settings(self, new: PetConfig) -> None:
        """按设置面板结果落地所有开关（窗口标志重建会重置样式，故穿透放最后）。"""
        self.set_mode(new.mode)
        self.set_size(new.size)
        self.set_autostart(new.autostart)
        self.set_topmost(new.topmost)
        self.set_passthrough(new.passthrough)
        # 端点 / Key / 音效
        self.cfg.api_key = new.api_key
        self.cfg.api_base = new.api_base
        self.cfg.model = new.model
        self.services.configure(
            api_key=new.api_key, api_base=new.api_base, model=new.model
        )
        self.cfg.sound = new.sound
        self.sound.enabled = new.sound
        save_config(self.cfg, default_config_path())
        self.say("设置已保存，下回开机也照旧～")

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Context:
            self.tray.setContextMenu(self._build_menu())
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visible()

    # ---------- 功能 ----------
    def set_mode(self, mode: str) -> None:
        self.mode = mode
        self.target = None
        self.cfg.mode = mode

    def set_size(self, mult: float) -> None:
        self.cur_h = sprite_height(mult)
        self.cfg.size = mult
        self.cross_t = 0.0
        self.prev_key = None
        self.win_mx = int(self.cur_h * 0.062) + 6
        self.win_w = max(
            p.width() for k, p in self.sprites.items() if k[1] == self.cur_h
        ) + self.win_mx * 2
        self.setFixedSize(self.win_w, self.cur_h + BUBBLE_H + MARGIN * 2 + 10)
        self.snap_into_screen()

    def snap_into_screen(self) -> None:
        geo = (self.screen() or QApplication.primaryScreen()).availableGeometry()
        x = max(geo.left(), min(geo.right() - self.width(), self.x()))
        y = max(geo.top(), min(geo.bottom() - self.height(), self.y()))
        self.move(x, y)
        self._sync_chat()

    def _apply_passthrough(self, on: bool) -> None:
        if sys.platform != "win32":
            return
        hwnd = int(self.winId())
        GWL_EXSTYLE, WS_EX_LAYERED, WS_EX_TRANSPARENT = -20, 0x80000, 0x20
        style = ctypes.windll.user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
        style |= WS_EX_LAYERED
        if on:
            style |= WS_EX_TRANSPARENT
        else:
            style &= ~WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)

    def set_passthrough(self, on: bool) -> None:
        self.cfg.passthrough = bool(on)
        self._apply_passthrough(bool(on))
        if on:
            self.say("我隐身了！右键托盘图标解除～")

    def set_topmost(self, on: bool) -> None:
        self.cfg.topmost = bool(on)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(on))
        self.show()

    def set_autostart(self, on: bool) -> None:
        self.cfg.autostart = bool(on)
        if sys.platform != "win32":
            self.say("仅支持 Windows 开机自启")
            return
        lnk = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
            "大肥鱼桌宠.lnk",
        )
        try:
            if on:
                target = sys.executable
                args = "" if getattr(sys, "frozen", False) else os.path.join(app_dir(), "桌宠.py")
                ps = (
                    "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{}');"
                    "$s.TargetPath='{}';$s.Arguments='\"{}\"';"
                    "$s.WorkingDirectory='{}';$s.Save()"
                ).format(lnk, target, args, app_dir())
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", ps],
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    check=False,
                )
                self.say("已开机自启，明天见～")
            else:
                if os.path.exists(lnk):
                    os.remove(lnk)
                self.say("已取消开机自启")
        except OSError as ex:
            QMessageBox.warning(self, "开机自启", f"设置失败：{ex}")

    def toggle_visible(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    def quit_app(self) -> None:
        self.cfg.x, self.cfg.y = self.x(), self.y()
        save_config(self.cfg, default_config_path())
        if self.tray:
            self.tray.hide()
        QApplication.quit()


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName(APP_NAME)
    win = PetWindow()
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as ex:  # noqa: BLE001
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, f"{APP_NAME} 出错", str(ex))
        except Exception:
            pass
        raise
