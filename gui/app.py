"""应用入口：创建 QApplication 与主窗口。"""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from gui.theme import apply_theme
from gui.window import MainWindow

APP_NAME = "BulkUnzip"


def main() -> int:
    """启动界面。"""
    if sys.platform != "win32":
        raise RuntimeError("BulkUnzip 图形界面仅支持 Windows。")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()


__all__ = ["main"]
