"""用 PyInstaller 打包 Windows 单文件程序。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NAME = "BulkUnzip"


def main() -> int:
    """构建 dist/BulkUnzip.exe，返回构建进程的退出码。"""
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile", "--windowed",
        "--name", NAME,
        "--paths", str(ROOT),
        str(ROOT / "main.py"),
    ]
    print(" ".join(command))
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
