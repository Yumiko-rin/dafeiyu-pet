# -*- coding: utf-8 -*-
"""日志系统：统一的日志配置。"""
from __future__ import annotations

import logging
import os
import sys


def setup_logger(name: str = "pet", level: int = logging.INFO) -> logging.Logger:
    """配置并返回日志记录器。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # 控制台输出
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # 文件输出（仅在有 app_dir 时）
    try:
        from .config import app_dir
        log_path = os.path.join(app_dir(), "pet.log")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass

    return logger


log = setup_logger()
