"""资源路径：源码与打包后都能找到 assets 目录。"""

from __future__ import annotations

import sys
from pathlib import Path


def asset_path(name: str) -> Path:
    """返回 assets 下某个文件的绝对路径。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "assets" / name


__all__ = ["asset_path"]
