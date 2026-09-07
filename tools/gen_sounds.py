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
    """大肥鱼点击叫声 —— 真正的哈基米！三连音：哈↗基↗米↗"""
    dur = 0.32
    n = int(SR * dur)
    # 三个音节的时间分界点
    t1 = int(n * 0.30)   # "哈" 结束
    t2 = int(n * 0.60)   # "基" 结束
    samples = []
    for i in range(n):
        t = i / SR
        # 包络：快速起音 + 三段振幅脉冲
        env = 1.0 - math.exp(-t / 0.003)
        # 三段振幅调制，每段一个脉冲
        if i < t1:
            pulse_env = math.sin(math.pi * i / t1)  # 半正弦脉冲
            f_base = 580 + 120 * math.sin(2 * math.pi * 2.5 * t)
        elif i < t2:
            pulse_env = math.sin(math.pi * (i - t1) / (t2 - t1))
            f_base = 720 + 150 * math.sin(2 * math.pi * 3.0 * (t - 0.096))
        else:
            pulse_env = math.sin(math.pi * (i - t2) / (n - t2))
            f_base = 880 + 180 * math.sin(2 * math.pi * 3.5 * (t - 0.192))
        env *= 0.7 + 0.3 * pulse_env
        # 颤音灵动
        vibrato = 20 * math.sin(2 * math.pi * 35 * t)
        f = f_base + vibrato
        # 基频
        s = math.sin(2 * math.pi * f * t)
        # 二次谐波（明亮）
        s += 0.5 * math.sin(2 * math.pi * f * 2 * t + 0.3)
        # 三次谐波（奶音）
        s += 0.2 * math.sin(2 * math.pi * f * 3 * t + 0.7)
        # 四次谐波（尖亮）
        s += 0.08 * math.sin(2 * math.pi * f * 4 * t + 1.1)
        samples.append(0.28 * s * env)
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
