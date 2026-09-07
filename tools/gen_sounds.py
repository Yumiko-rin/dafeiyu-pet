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


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out_dir = os.path.join(os.path.dirname(here), "sounds")
    os.makedirs(out_dir, exist_ok=True)
    _write(os.path.join(out_dir, "pop.wav"), gen_pop())
    _write(os.path.join(out_dir, "ding.wav"), gen_ding())


if __name__ == "__main__":
    main()
