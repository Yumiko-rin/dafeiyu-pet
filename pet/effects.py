# -*- coding: utf-8 -*-
"""桌宠特效系统：粒子 + 发光 + 闪光环 + 拖尾 + 落地扬尘。

设计要点：
- EffectSystem 只负责「生成并更新粒子状态」，不碰 Qt 绘制调度；
  draw(painter, cx, cy) 由 pet_window.paintEvent 在精灵层之后统一调用。
- 粒子用 math 手算位移（无物理引擎依赖），上限 120 颗，超出按 life 最低剔除。
- fx_enabled=False 时所有 trigger / update / draw 全部 short-circuit，
  低性能机或不喜欢特效可一键关闭，零开销。
- 爱心 / 星光 / 闪光环 / 拖尾 / 尘土 5 类粒子，按场景组合触发。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QPainterPath,
    QPen,
    QRadialGradient,
)

# 粒子硬上限：超出按 life 最低剔除，避免帧率塌陷
MAX_PARTICLES = 120


@dataclass
class Particle:
    """单个粒子状态。坐标相对桌宠中心（paintEvent 传入 cx, cy 做平移）。"""
    x: float
    y: float
    vx: float
    vy: float
    life: float            # 剩余秒数
    max_life: float
    size: float
    color: Tuple[int, int, int, int]  # r,g,b,a（0-255）
    kind: str              # "heart" | "spark" | "dust" | "ring" | "star"
    rot: float = 0.0       # 旋转角（rad），用于星光/爱心朝向
    spin: float = 0.0      # 旋转速度（rad/s）


@dataclass
class GlowState:
    """空闲呼吸发光状态（非粒子，统一由 EffectSystem 管理）。"""
    t: float = 0.0          # 累计时间
    enabled: bool = True


class EffectSystem:
    """桌宠特效总管：粒子池 + 发光呼吸 + 触发接口。"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.particles: List[Particle] = []
        self.glow = GlowState(enabled=enabled)
        self._glow_color: Tuple[int, int, int] = (140, 128, 255)

    # ---------- 开关 ----------
    def set_enabled(self, on: bool) -> None:
        self.enabled = bool(on)
        self.glow.enabled = bool(on)
        if not on:
            self.particles.clear()

    def set_theme(self, theme_colors: dict) -> None:
        self._glow_color = tuple(theme_colors.get("glow", (140, 128, 255)))

    # ---------- 触发器 ----------
    def click_burst(self, x: float, y: float) -> None:
        """单击：4-6 颗爱心向上飘散 + 1 圈白色闪光环扩散。"""
        if not self.enabled:
            return
        n = random.randint(4, 6)
        for _ in range(n):
            ang = random.uniform(-math.pi * 0.75, -math.pi * 0.25)  # 向上半圆
            spd = random.uniform(60, 120)
            life = random.uniform(0.8, 1.2)
            self._add(Particle(
                x=x, y=y,
                vx=math.cos(ang) * spd,
                vy=math.sin(ang) * spd - 30,  # 额外上飘
                life=life, max_life=life,
                size=random.uniform(10, 16),
                color=(255, 120, 180, 230),
                kind="heart",
                rot=random.uniform(0, math.pi * 2),
                spin=random.uniform(-2, 2),
            ))
        # 闪光环
        self._add(Particle(
            x=x, y=y, vx=0, vy=0,
            life=0.4, max_life=0.4,
            size=8,
            color=(255, 255, 255, 220),
            kind="ring",
        ))

    def drag_trail(self, x: float, y: float, dx: float, dy: float) -> None:
        """拖拽中：蓝紫色拖尾粒子，跟随移动方向衰减。"""
        if not self.enabled:
            return
        # 限频：已有同类粒子够多就少生
        if sum(1 for p in self.particles if p.kind == "spark") > 24:
            return
        spd = math.hypot(dx, dy)
        if spd < 1:
            return
        life = random.uniform(0.3, 0.5)
        self._add(Particle(
            x=x + random.uniform(-4, 4),
            y=y + random.uniform(-4, 4),
            vx=-dx * 0.15 + random.uniform(-20, 20),
            vy=-dy * 0.15 + random.uniform(-20, 20),
            life=life, max_life=life,
            size=random.uniform(3, 6),
            color=(140, 128, 255, 200),
            kind="spark",
        ))

    def land_dust(self, x: float, y: float) -> None:
        """落地：扁平尘土向两侧水平扩散。"""
        if not self.enabled:
            return
        for side in (-1, 1):
            for _ in range(3):
                life = random.uniform(0.4, 0.7)
                self._add(Particle(
                    x=x + side * 6,
                    y=y,
                    vx=side * random.uniform(40, 90),
                    vy=random.uniform(-20, -5),
                    life=life, max_life=life,
                    size=random.uniform(4, 8),
                    color=(180, 175, 200, 160),
                    kind="dust",
                ))

    def poke_sparkle(self, x: float, y: float) -> None:
        """被戳一戳：小星光闪烁（比 click_burst 更轻柔）。"""
        if not self.enabled:
            return
        for _ in range(3):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(20, 50)
            life = random.uniform(0.5, 0.8)
            self._add(Particle(
                x=x, y=y,
                vx=math.cos(ang) * spd,
                vy=math.sin(ang) * spd,
                life=life, max_life=life,
                size=random.uniform(4, 8),
                color=(255, 220, 130, 220),
                kind="star",
                rot=random.uniform(0, math.pi),
                spin=random.uniform(-3, 3),
            ))

    # ---------- 更新 ----------
    def update(self, dt: float) -> None:
        if not self.enabled:
            return
        self.glow.t += dt
        alive: List[Particle] = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            # 尘土受重力，爱心/星光轻微上飘衰减
            if p.kind == "dust":
                p.vy += 200 * dt  # 重力
            elif p.kind in ("heart", "star"):
                p.vy += 40 * dt   # 轻微下落抵消上飘
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.rot += p.spin * dt
            alive.append(p)
        self.particles = alive
        # 超上限按 life 最低剔除
        if len(self.particles) > MAX_PARTICLES:
            self.particles.sort(key=lambda q: q.life, reverse=True)
            self.particles = self.particles[:MAX_PARTICLES]

    # ---------- 绘制 ----------
    def draw(self, painter, cx: float, cy: float) -> None:
        """由 paintEvent 在精灵层之后调用。cx/cy = 桌宠中心点。"""
        if not self.enabled:
            return
        painter.save()
        painter.setRenderHint(painter.RenderHint.Antialiasing, True)
        # 空闲呼吸发光（在精灵下层；这里先画，会被精灵盖住部分，形成光晕透出）
        if self.glow.enabled:
            self._draw_glow(painter, cx, cy)
        # 粒子层
        for p in self.particles:
            a = max(0.0, min(1.0, p.life / p.max_life))
            r, g, b, base_a = p.color
            col = QColor(r, g, b, int(base_a * a))
            if p.kind == "heart":
                self._draw_heart(painter, cx + p.x, cy + p.y, p.size, col, p.rot)
            elif p.kind == "ring":
                self._draw_ring(painter, cx + p.x, cy + p.y, p.size, p.max_life - p.life, col)
            elif p.kind == "dust":
                self._draw_dust(painter, cx + p.x, cy + p.y, p.size, col)
            elif p.kind == "star":
                self._draw_star(painter, cx + p.x, cy + p.y, p.size, col, p.rot)
            elif p.kind == "spark":
                self._draw_spark(painter, cx + p.x, cy + p.y, p.size, col)
        painter.restore()

    # ---------- 内部绘制 ----------
    def _draw_glow(self, painter, cx: float, cy: float) -> None:
        """精灵四周柔和发光呼吸。"""
        breath = 0.5 + 0.5 * math.sin(self.glow.t * 2.0)
        radius = 120 + breath * 20
        grad = QRadialGradient(QPointF(cx, cy), radius)
        r, g, b = self._glow_color
        c = QColor(r, g, b, int(20 + breath * 25))
        grad.setColorAt(0.0, c)
        grad.setColorAt(1.0, QColor(r, g, b, 0))
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(grad))
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

    def _draw_heart(self, painter, x, y, size, color, rot) -> None:
        """心形路径 + 渐变填充。"""
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(rot))
        path = QPainterPath()
        s = size / 16.0
        path.moveTo(0, 5 * s)
        path.cubicTo(-8 * s, -3 * s, -4 * s, -11 * s, 0, -5 * s)
        path.cubicTo(4 * s, -11 * s, 8 * s, -3 * s, 0, 5 * s)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(color))
        painter.drawPath(path)
        painter.restore()

    def _draw_ring(self, painter, x, y, base_size, age, color) -> None:
        """闪光环：半径随 age 扩大，透明度衰减。"""
        radius = base_size + age * 40
        a = max(0.0, 1.0 - age / 0.4)
        pen = QPen(QColor(color.red(), color.green(), color.blue(), int(color.alpha() * a)))
        pen.setWidthF(2.5)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawEllipse(QPointF(x, y), radius, radius)

    def _draw_dust(self, painter, x, y, size, color) -> None:
        """扁平尘土椭圆。"""
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(x, y), size * 1.4, size * 0.7)

    def _draw_star(self, painter, x, y, size, color, rot) -> None:
        """五角星（内外半径交替）。"""
        painter.save()
        painter.translate(x, y)
        painter.rotate(math.degrees(rot))
        path = QPainterPath()
        outer = size
        inner = size * 0.4
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = outer if i % 2 == 0 else inner
            px, py = math.cos(ang) * r, math.sin(ang) * r
            if i == 0:
                path.moveTo(px, py)
            else:
                path.lineTo(px, py)
        path.closeSubpath()
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(color))
        painter.drawPath(path)
        painter.restore()

    def _draw_spark(self, painter, x, y, size, color) -> None:
        """拖尾小圆点。"""
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(color))
        painter.drawEllipse(QPointF(x, y), size, size)

    # ---------- 工具 ----------
    def _add(self, p: Particle) -> None:
        if len(self.particles) < MAX_PARTICLES:
            self.particles.append(p)
