# -*- coding: utf-8 -*-
"""大肥鱼桌宠 —— 程序入口。

与系统监控台（main.py）并存、互不影响，独立启动：
    python 桌宠.py
"""
import sys

from pet.pet_window import main

if __name__ == "__main__":
    sys.exit(main())
