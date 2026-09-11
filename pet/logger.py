# -*- coding: utf-8 -*-
"""日志系统：统一的日志配置，带轮转防爆。"""
from __future__ import annotations

import logging
import logging.handlers
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

    # 文件输出（带轮转，最多 3 个 1MB 文件）
    try:
        from .config import app_dir
        log_path = os.path.join(app_dir(), "pet.log")
        fh = logging.handlers.RotatingFileHandler(
            log_path, maxBytes=1024 * 1024, backupCount=3, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass

    return logger


log = setup_logger()
