# -*- coding: utf-8 -*-
"""合成桌宠音效（纯标准库，无外部依赖）。

输出：
- sounds/pop.wav   单击蹦跳 / 戳一戳的轻"啵"
- sounds/ding.wav  收到回复的轻"叮"

运行：python tools/gen_sounds.py
"""
from __future__ import annotations

import math
import os
import wave

SR = 44100


def _to_frames(samples):
    """float[-1,1] -> 16bit 帧，归一化到峰值 0.9 防削顶。"""
    peak = max((abs(s) for s in samples), default=1.0) or 1.0
    gain = 0.9 / peak
    out = bytearray()
    for s in samples:
        v = int(max(-1.0, min(1.0, s * gain)) * 32767)
        out += v.to_bytes(2, "little", signed=True)
    return bytes(out)


def _write(path, samples):
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(_to_frames(samples))
    print("written:", path, f"({len(samples)/SR:.2f}s)")


def gen_pop():
    dur = 0.09
    n = int(SR * dur)
    samples = []
    for i in range(n):
        t = i / SR
        env = math.exp(-t / 0.025)
        f = 520 - 220 * (t / dur)
        s = math.sin(2 * math.pi * f * t) * env
        samples.append(0.35 * s)
    return samples


def gen_ding():
    dur = 0.55
    n = int(SR * dur)
    samples = []
    for i in range(n):
        t = i / SR
        env = math.exp(-t / 0.18)
        s = (
            math.sin(2 * math.pi * 880 * t)
            + 0.5 * math.sin(2 * math.pi * 1320 * t)
            + 0.3 * math.sin(2 * math.pi * 1760 * t)
        ) * env
        samples.append(0.28 * s)
    return samples


def gen_mew():
    """大肥鱼点击叫声 —— 哈基米风格！高音 + 上滑 + 奶音，超级可爱。"""
    dur = 0.25
    n = int(SR * dur)
    mid = int(n * 0.35)
    samples = []
    for i in range(n):
        t = i / SR
        # 包络：极快起音(3ms) + 自然衰减
        env = 1.0 - math.exp(-t / 0.003)
        env *= math.exp(-t / 0.13)
        # 频率轨迹：先升到高音再抖一下，模仿哈基米的上扬喵叫
        if i < mid:
            phase = i / mid
            f_base = 550 + 350 * phase
        else:
            phase = (i - mid) / (n - mid)
            f_base = 900 - 200 * phase + 80 * math.sin(2 * math.pi * 3 * phase)
        # 高频颤音增加灵动感
        vibrato = 22 * math.sin(2 * math.pi * 38 * t)
        f = f_base + vibrato
        # 基频
        s = math.sin(2 * math.pi * f * t)
        # 二次谐波（明亮）
        s += 0.55 * math.sin(2 * math.pi * f * 2 * t + 0.3)
        # 三次谐波（奶音）
        s += 0.25 * math.sin(2 * math.pi * f * 3 * t + 0.7)
        # 四次谐波（增加"哈基米"特有的尖亮感）
        s += 0.1 * math.sin(2 * math.pi * f * 4 * t + 1.1)
        samples.append(0.30 * s * env)
    return samples


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(here), "sounds")
    os.makedirs(out_dir, exist_ok=True)
    _write(os.path.join(out_dir, "pop.wav"), gen_pop())
    _write(os.path.join(out_dir, "ding.wav"), gen_ding())
    _write(os.path.join(out_dir, "mew.wav"), gen_mew())


if __name__ == "__main__":
    main()
