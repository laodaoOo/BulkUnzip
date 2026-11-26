"""应用入口：创建 QApplication 与主窗口。"""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from gui.resources import asset_path
from gui.version import APP_VERSION
from gui.window import MainWindow

APP_NAME = "BulkUnzip"


def main() -> int:
    """启动界面。"""
    if sys.platform != "win32":
        raise RuntimeError("BulkUnzip 图形界面仅支持 Windows。")
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_NAME)
    app.setWindowIcon(QIcon(str(asset_path("app.ico"))))
    window = MainWindow()
    window.show()
    return app.exec()


__all__ = ["main"]
