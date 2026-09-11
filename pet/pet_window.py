# -*- coding: utf-8 -*-
"""大肥鱼桌宠主窗口：三视图透明桌宠 + 动画 + 交互 + 托盘 + 粒子特效。

- 左键按住：拖拽（侧身朝向拖动方向），拖尾粒子跟随
- 单击：蹦跳 + 爱心粒子飘散 + 闪光环 + 回嘴
- 右键菜单：打开各种功能面板（时钟/倒计时/系统监控等）
- 右键 / 托盘：完整菜单（含可视化设置面板）
- 摸鱼氛围：空闲时随机戳一戳 / 自发碎碎念 / 眨眼 / 打哈欠 / 睡觉
- 特效层：粒子（爱心/星光/拖尾/扬尘）+ 空闲呼吸发光
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
    QRadialGradient,
    QPen,
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
from .effects import EffectSystem
from .lines import LINES, REACT_LINES, INNER_LINES, DRAG_LINES, MUTTER_LINES, POKE_LINES
from .logger import log
from .sound import SoundManager
from .styles import THEMES
from .settings import SettingsDialog
from .notifications import NotificationManager

# 功能面板
from .panels.clock_calendar import ClockCalendarPanel
from .panels.countdown import CountdownPanel
from .panels.system_monitor import SystemMonitorPanel
from .panels.sticky_notes import StickyNotesPanel
from .panels.pomodoro import PomodoroPanel
from .panels.clipboard_history import ClipboardHistoryPanel
from .panels.quick_launcher import QuickLauncherPanel
from .panels.weather import WeatherPanel
from .panels.guess_number import GuessNumberPanel
from .panels.fish_time import FishTimePanel

BUBBLE_H = 56
BUBBLE_DUR = 2.8
BUBBLE_FADE_IN = 0.16
BUBBLE_FADE_OUT = 0.22
MARGIN = 4
SPEED = 380.0
TICK = 20

IDLE_ACTIONS = ("jump", "sway", "stretch", "blink", "yawn", "sleep", "speak_inner", "speak")


class PetWindow(QWidget):
    """透明桌宠窗口。"""

    def __init__(self):
        self.cfg: PetConfig = load_config(default_config_path())
        self.sound = SoundManager(enabled=self.cfg.sound)
        self.fx = EffectSystem(enabled=self.cfg.fx_enabled)

        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if self.cfg.topmost:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        super().__init__(None, flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle(APP_NAME)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.fx.set_theme(THEMES.get(self.cfg.theme, THEMES["默认紫"]))
        self.notifier = NotificationManager(self)
        self.notifier.on_notify(lambda msg: self.say(msg))

        self._load_sprites()
        self._init_state()
        self._init_hotkeys()
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

        log.info("桌宠启动")

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
        self.action_dur = 0.0
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
        self.last_drag_pos = None
        self.last_line = ""
        self.bubble_font = QFont("Microsoft YaHei UI", 11)
        self._was_moving = False

        # 功能面板实例（延迟初始化）
        self._panels = {}

    def _init_hotkeys(self) -> None:
        """初始化快捷键。"""
        from .hotkeys import HotkeyManager
        self._hotkeys = HotkeyManager(self)
        self._hotkeys.register("toggle_visible", "Ctrl+Shift+F10", self.toggle_visible)
        self._hotkeys.register("open_clock", "Ctrl+Shift+F1", lambda: self._open_panel("clock"))
        self._hotkeys.register("open_monitor", "Ctrl+Shift+F2", lambda: self._open_panel("monitor"))
        self._hotkeys.register("open_notes", "Ctrl+Shift+F3", lambda: self._open_panel("notes"))
        self._hotkeys.register("open_clipboard", "Ctrl+Shift+F4", lambda: self._open_panel("clipboard"))

    def _get_panel(self, name: str):
        """懒加载功能面板。"""
        if name not in self._panels:
            panel_map = {
                "clock": ClockCalendarPanel,
                "countdown": CountdownPanel,
                "monitor": SystemMonitorPanel,
                "notes": StickyNotesPanel,
                "pomodoro": PomodoroPanel,
                "clipboard": ClipboardHistoryPanel,
                "launcher": QuickLauncherPanel,
                "weather": WeatherPanel,
                "guess": GuessNumberPanel,
                "fish": FishTimePanel,
            }
            cls = panel_map.get(name)
            if cls:
                panel = cls(self)
                self._panels[name] = panel
                # 连接完成信号到桌宠通知
                if name == "countdown" and hasattr(panel, "alarm"):
                    panel.alarm.connect(lambda msg: self.say(f"⏰ {msg}"))
                if name == "pomodoro" and hasattr(panel, "pomodoro_done"):
                    panel.pomodoro_done.connect(lambda: self.say("番茄钟完成！休息一下~"))
        return self._panels.get(name)

    def _open_panel(self, name: str) -> None:
        """打开指定功能面板。"""
        panel = self._get_panel(name)
        if panel:
            self.sound.play("pop")
            x, y = self._panel_position(panel)
            panel.popup_at(x, y)

    def _panel_position(self, panel: QWidget) -> Tuple[int, int]:
        """计算面板应出现的坐标：桌宠头顶、水平居中。"""
        pw, ph = panel.width(), panel.height()
        geo = self._current_screen_geo()
        cx = self.x() + self.width() // 2
        x = int(cx - pw / 2)
        y = int(self.y() - ph - 12)
        if y < geo.top():
            y = int(self.y() + self.height() + 12)
        x = max(geo.left(), min(geo.right() - pw, x))
        if y + ph > geo.bottom():
            y = geo.top()
        return x, y

    def _build_panels(self) -> None:
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._on_single_click)

        self._ambient_timer = QTimer(self)
        self._ambient_timer.setInterval(90000)
        self._ambient_timer.timeout.connect(self._ambient_tick)
        self._ambient_timer.start()

    def _build_tray(self) -> None:
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self.icon, self)
        tray_menu = self._build_menu()
        self.tray.setContextMenu(tray_menu)
        tray_menu.deleteLater()
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        now = self.t * TICK / 1000.0

        if self.bubble_text:
            self._draw_bubble(p, now)

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
        act_alpha = 1.0
        if self.action == "sway":
            act_rot = math.sin(self.action_t * 3.14159 * 2) * 10 * self.action_t
        elif self.action == "stretch":
            act_sy = 0.06 * math.sin(self.action_t * 3.14159)
            act_sx = -0.03 * math.sin(self.action_t * 3.14159)
        elif self.action == "blink":
            act_sy = -0.04 * math.sin(self.action_t * 3.14159)
        elif self.action == "yawn":
            act_sy = 0.04 * math.sin(self.action_t * 3.14159)
        elif self.action == "sleep":
            act_sy = 0.03 * math.sin(self.action_t * 3.14159 * 0.5)
            act_alpha = 0.78

        self.fx.draw(p, cx, BUBBLE_H + MARGIN + self.cur_h / 2)

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
            p.setOpacity(opacity * act_alpha)
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

        self._draw_shadow(p, cx, BUBBLE_H + MARGIN + self.cur_h, jump, bob)

    def _draw_shadow(self, p, cx, bottom, jump, bob) -> None:
        lift = abs(jump) / 14.0 + abs(bob) / 7.0
        alpha = max(20, int(80 * (1.0 - lift)))
        rx = 40 - lift * 10
        ry = 9 - lift * 3
        p.save()
        p.setPen(QPen(Qt.PenStyle.NoPen))
        p.setBrush(QBrush(QColor(24, 18, 70, alpha)))
        p.drawEllipse(QPointF(cx, bottom + 4), rx, ry)
        p.restore()

    def _draw_bubble(self, p, now) -> None:
        now_in = (now - self.bubble_in_at) / BUBBLE_FADE_IN
        in_a = max(0.0, min(1.0, now_in)) if now_in >= 0.0 else 0.0
        if now < self.bubble_until:
            out_a = 1.0
        else:
            out_a = max(0.0, (self.bubble_until + BUBBLE_FADE_OUT - now) / BUBBLE_FADE_OUT)
        alpha = in_a * out_a
        if alpha <= 0.004 or now >= self.bubble_until + BUBBLE_FADE_OUT:
            return
        bfont = QFont(self.bubble_font)
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
        for i, dy in enumerate((3.4, 2.1, 1.0)):
            p.setBrush(QColor(24, 18, 70, max(4, 30 - i * 11)))
            p.drawRoundedRect(QRectF(bx, by + dy, bw, bh), radius, radius)
        grad = QLinearGradient(0, by, 0, by + bh)
        grad.setColorAt(0.0, top_c)
        grad.setColorAt(1.0, bot_c)
        p.setBrush(QBrush(grad))
        p.setPen(QColor(border_c.red(), border_c.green(), border_c.blue(), int(border_c.alpha() * alpha)))
        p.drawRoundedRect(rect, radius, radius)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(tail_c)
        tail = QPointF(self.width() / 2, by + bh)
        p.drawPolygon(
            QPolygonF([tail, QPointF(tail.x() - 7, tail.y() + 9), QPointF(tail.x() + 7, tail.y() + 9)])
        )
        if accent:
            p.setBrush(QColor(255, 205, 120, 235))
            p.drawRoundedRect(QRectF(bx + 6, by + 8, 3, bh - 16), 1.5, 1.5)
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

    def tick(self) -> None:
        self.t += 1
        dt = TICK / 1000.0
        self.fx.update(dt)

        if self.jump_t > 0:
            self.jump_t = max(0.0, self.jump_t - 0.06)
        if self.cross_t > 0:
            self.cross_t = max(0.0, self.cross_t - 0.15)
        if self.action_t > 0:
            self.action_t = max(0.0, self.action_t - dt)
            if self.action_t <= 0:
                self.action = None
                self.action_t = 0.0

        if self.dragging:
            self.update()
            return

        any_panel_visible = any(
            p.isVisible() for p in self._panels.values()
        ) if self._panels else False
        if any_panel_visible:
            self.target = None
            self.update()
            return

        now_ms = self.t * TICK

        if self.mode == "follow":
            self._tick_follow()
        elif self.mode == "wander":
            self._tick_wander(now_ms)
        else:
            self._maybe_idle_action()
            self.update()
            return

        self._tick_move()
        self.update()

    def _tick_follow(self) -> None:
        """跟随鼠标模式的 tick 逻辑。"""
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

    def _tick_wander(self, now_ms: int) -> None:
        """自由散步模式的 tick 逻辑。"""
        if self.target is None:
            if now_ms < self.rest_until:
                self._maybe_idle_action()
                self.update()
                return
            geo = self._current_screen_geo()
            self.target = (
                random.randint(geo.left() + 40, geo.right() - self.width() - 40),
                random.randint(geo.top() + 40, geo.bottom() - self.height() - 40),
            )

    def _tick_move(self) -> None:
        """通用移动逻辑：朝目标移动并更新朝向。"""
        if self.target is None:
            return
        cx, cy = self.x() + self.width() / 2, self.y() + self.height() / 2
        dx, dy = self.target[0] - cx, self.target[1] - cy
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 12:
            self.target = None
            self.rest_until = self.t * TICK + random.randint(8000, 18000)
            self._set_dir("down")
            self.fx.land_dust(cx - self.x(), self.cur_h)
        else:
            step = self.cur_speed * TICK / 1000.0
            nx, ny = cx + dx / dist * step, cy + dy / dist * step
            self.move(int(nx - self.width() / 2), int(ny - self.height() / 2))
            if abs(dx) > abs(dy) * 1.15:
                self._set_dir("left" if dx < 0 else "right", 1 if dx < 0 else -1)
            else:
                self._set_dir("up" if dy < 0 else "down")
        if random.random() < 0.002 and self.jump_t == 0:
            self.jump_t = 0.5

        target_speed = SPEED if self.target is not None else 0.0
        self.cur_speed += (target_speed - self.cur_speed) * 0.3

    def _maybe_idle_action(self) -> None:
        if random.random() < 0.012:
            pick = random.random()
            if pick < 0.22:
                self.jump_t = 1.0
            elif pick < 0.40:
                self.action, self.action_t, self.action_dur = "sway", 1.0, 1.0
            elif pick < 0.55:
                self.action, self.action_t, self.action_dur = "stretch", 1.0, 1.0
            elif pick < 0.72:
                self.action, self.action_t, self.action_dur = "blink", 0.35, 0.35
            elif pick < 0.85:
                self.action, self.action_t, self.action_dur = "yawn", 1.2, 1.2
            elif pick < 0.92:
                self.action, self.action_t, self.action_dur = "sleep", 4.0, 4.0
                self.say("Zzz…", inner=True)
            else:
                if self.t - self.last_speak_tick >= 1500:
                    self.last_speak_tick = self.t
                    self.say(random.choice(INNER_LINES), inner=True)

    def _ambient_tick(self) -> None:
        any_visible = any(p.isVisible() for p in self._panels.values()) if self._panels else False
        if any_visible or self.dragging:
            return
        if random.random() < 0.5:
            line = random.choice(POKE_LINES)
            self.say(line)
            self.sound.play("pop")
            self.fx.poke_sparkle(self.width() / 2, self.cur_h / 2)
        else:
            self.say(random.choice(MUTTER_LINES))

    def say(self, text: str, inner: bool = False) -> None:
        now = self.t * TICK / 1000.0
        if text == self.last_line and now < self.bubble_until:
            return
        self.last_line = text
        self.bubble_inner = inner
        self.bubble_text = f"（{text}）" if inner else text
        self.bubble_in_at = now
        self.bubble_until = now + BUBBLE_DUR
        self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.globalPosition().toPoint()
            self.dragging = False
            self.last_drag_pos = None
            self._was_moving = False

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton and self.drag_start_pos is not None:
            delta = event.globalPosition().toPoint() - self.drag_start_pos
            if not self.dragging and delta.manhattanLength() > 6:
                self.dragging = True
                self.drag_offset = event.globalPosition().toPoint() - QPoint(self.x(), self.y())
                self.last_drag_pos = event.globalPosition().toPoint()
            if self.dragging and self.drag_offset is not None:
                pos = event.globalPosition().toPoint() - self.drag_offset
                self.move(pos)
                if abs(delta.x()) > 10:
                    self._set_dir("left" if delta.x() < 0 else "right", 1 if delta.x() < 0 else -1)
                if self.last_drag_pos is not None:
                    cur_pos = event.globalPosition().toPoint()
                    ddx = cur_pos.x() - self.last_drag_pos.x()
                    ddy = cur_pos.y() - self.last_drag_pos.y()
                    if abs(ddx) + abs(ddy) > 3:
                        self.fx.drag_trail(self.width() / 2, self.cur_h / 2, -ddx, -ddy)
                        self._was_moving = True
                self.last_drag_pos = event.globalPosition().toPoint()
                self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                self.dragging = False
                self.drag_offset = None
                self.drag_start_pos = None
                self._set_dir("down", 1)
                self.target = None
                self.rest_until = self.t * TICK + random.randint(6000, 14000)
                if self._was_moving:
                    self.fx.land_dust(self.width() / 2, self.cur_h)
                if random.random() < 0.5:
                    self.say(random.choice(DRAG_LINES))
            else:
                self._click_timer.start(280)
            self.drag_start_pos = None
            self.last_drag_pos = None

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._click_timer.stop()
            self._open_panel("clock")

    def _on_single_click(self) -> None:
        self.sound.play("mew")
        self.fx.click_burst(self.width() / 2, self.cur_h / 2)
        if random.random() < 0.7:
            self.jump_t = 1.0
        if random.random() < 0.6:
            self.say(random.choice(REACT_LINES))

    def contextMenuEvent(self, event) -> None:
        menu = self._build_menu()
        menu.exec(event.globalPos())
        menu.deleteLater()

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

        m.addSeparator()

        func_menu = m.addMenu("功能面板")
        func_menu.addAction("桌面时钟", lambda: self._open_panel("clock"))
        func_menu.addAction("倒计时提醒", lambda: self._open_panel("countdown"))
        func_menu.addAction("系统监控", lambda: self._open_panel("monitor"))
        func_menu.addAction("便签备忘录", lambda: self._open_panel("notes"))
        func_menu.addAction("番茄钟", lambda: self._open_panel("pomodoro"))
        func_menu.addAction("剪贴板历史", lambda: self._open_panel("clipboard"))
        func_menu.addAction("快捷启动器", lambda: self._open_panel("launcher"))
        func_menu.addAction("天气", lambda: self._open_panel("weather"))
        func_menu.addAction("猜数字游戏", lambda: self._open_panel("guess"))
        func_menu.addAction("摸鱼计时器", lambda: self._open_panel("fish"))

        m.addSeparator()
        m.addAction("设置…", self._open_settings)
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
        fa = m.addAction("粒子特效")
        fa.setCheckable(True)
        fa.setChecked(self.cfg.fx_enabled)
        fa.triggered.connect(self.set_fx)
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
        self.set_mode(new.mode)
        self.set_size(new.size)
        self.set_autostart(new.autostart)
        self.set_topmost(new.topmost)
        self.set_passthrough(new.passthrough)
        self.set_fx(new.fx_enabled)
        self.cfg.theme = new.theme
        self.fx.set_theme(THEMES.get(new.theme, THEMES["默认紫"]))
        self.cfg.sound = new.sound
        self.sound.enabled = new.sound
        save_config(self.cfg, default_config_path())
        self.say("设置已保存，下回开机也照旧～")

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Context:
            menu = self._build_menu()
            self.tray.setContextMenu(menu)
            menu.deleteLater()
        elif reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visible()

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

    def set_fx(self, on: bool) -> None:
        self.cfg.fx_enabled = bool(on)
        self.fx.set_enabled(bool(on))
        if on:
            self.say("特效开啦，看好看好～")
        else:
            self.say("特效关了，清清爽爽～")

    def snap_into_screen(self) -> None:
        geo = self._current_screen_geo()
        x = max(geo.left(), min(geo.right() - self.width(), self.x()))
        y = max(geo.top(), min(geo.bottom() - self.height(), self.y()))
        self.move(x, y)

    def _current_screen_geo(self):
        """获取桌宠当前所在屏幕的可用区域。"""
        screen = self.screen()
        if screen is None:
            # 找到桌宠中心所在的屏幕
            cx = self.x() + self.width() / 2
            cy = self.y() + self.height() / 2
            for s in QApplication.screens():
                geo = s.availableGeometry()
                if geo.left() <= cx <= geo.right() and geo.top() <= cy <= geo.bottom():
                    return geo
        return (screen or QApplication.primaryScreen()).availableGeometry()

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
    except Exception as ex:
        try:
            app = QApplication.instance() or QApplication(sys.argv)
            QMessageBox.critical(None, f"{APP_NAME} 出错", str(ex))
        except Exception:
            pass
        raise
