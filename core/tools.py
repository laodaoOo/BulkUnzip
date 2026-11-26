"""归档工具查找与解压命令：7-Zip 负责 zip / 7z，WinRAR 负责 rar。"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

# 各格式可接受的工具名，用于在 PATH 中查找。
PATH_NAMES = {
    "7z": ("7z.exe", "7za.exe", "7zz.exe"),
    "rar": ("Rar.exe", "rar.exe"),
}

# 安装目录名：Program Files 下对应的子目录。
INSTALL_HINTS = {"7z": "7-Zip", "rar": "WinRAR"}


def application_directory() -> Path:
    """打包后取 exe 所在目录，源码运行时取项目根目录。"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def _install_roots(subdirectory: str) -> list[Path]:
    """常见安装根目录：Program Files、Program Files (x86)、用户目录。"""
    roots = []
    for variable in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        value = os.environ.get(variable)
        if not value:
            continue
        base = Path(value)
        roots.append(base / "Programs" / subdirectory if variable == "LOCALAPPDATA"
                     else base / subdirectory)
    return roots


def find_tool(kind: str) -> Path | None:
    """按程序目录、安装目录、PATH 的顺序查找命令行工具。"""
    base = application_directory()
    candidates = [base / "dependencies" / kind / name for name in PATH_NAMES[kind]]
    candidates.extend(
        root / name
        for root in _install_roots(INSTALL_HINTS[kind])
        for name in PATH_NAMES[kind]
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    for name in PATH_NAMES[kind]:
        located = shutil.which(name)
        if located:
            return Path(located)
    return None


def resolve_tool(kind: str, configured: str) -> Path | None:
    """解析配置里的工具路径；空值或 auto 表示自动查找。"""
    text = configured.strip()
    if not text or text.lower() == "auto":
        return find_tool(kind)
    path = Path(text)
    if not path.is_file():
        raise ValueError(f"找不到 {kind} 命令行工具：{path}")
    return path


def extract_command(tool: Path, kind: str, archive: Path, target: Path) -> list[str]:
    """构造解压到 target 的命令行参数，并让工具输出百分比进度。"""
    if kind == "rar":
        return [str(tool), "x", "-y", "-o+", str(archive), str(target) + os.sep]
    return [str(tool), "x", "-y", "-bsp1", f"-o{target}", str(archive)]


__all__ = [
    "application_directory",
    "extract_command",
    "find_tool",
    "resolve_tool",
]
