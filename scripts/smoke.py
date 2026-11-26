"""启动自检：按真实入口构建一次窗口，事件循环立即返回。

用于在打包前发现入口层的签名/导入错误（例如 apply_theme 参数不匹配）。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import gui.app as app_module  # noqa: E402


class _SmokeApplication(app_module.QApplication):  # type: ignore[misc]
    """不进入事件循环的 QApplication。"""

    def exec(self) -> int:
        return 0


def main() -> int:
    """执行真实入口，成功返回 0。"""
    app_module.QApplication = _SmokeApplication
    return app_module.main()


if __name__ == "__main__":
    raise SystemExit(main())
