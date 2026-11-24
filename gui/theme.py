"""界面配色：Windows 经典工具风格（7-Zip 式），浅灰底、方角、紧凑控件。"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

WINDOW = "#F0F0F0"
PANEL = "#F5F5F5"
LIST = "#FFFFFF"
BORDER = "#A0A0A0"
SOFT_BORDER = "#C8C8C8"
TEXT = "#1A1A1A"
MUTED = "#5A5A5A"
SELECTION = "#CCE8FF"
ACCENT = "#2F5D8C"

STYLE_SHEET = f"""
QWidget {{ color: {TEXT}; font-family: "Microsoft YaHei UI"; font-size: 12px; }}
QMainWindow, QWidget#root {{ background: {WINDOW}; }}
QMenuBar {{ background: {WINDOW}; border-bottom: 1px solid {SOFT_BORDER}; }}
QMenuBar::item {{ padding: 3px 8px; background: transparent; }}
QMenuBar::item:selected {{ background: {SELECTION}; }}
QMenu {{ background: {LIST}; border: 1px solid {BORDER}; }}
QMenu::item {{ padding: 4px 24px 4px 20px; }}
QMenu::item:selected {{ background: {SELECTION}; color: {TEXT}; }}
QToolBar {{ background: {PANEL}; border-bottom: 1px solid {BORDER}; spacing: 2px; padding: 2px; }}
QToolBar::separator {{ width: 1px; background: {SOFT_BORDER}; margin: 4px 6px; }}
QToolButton {{ padding: 3px 8px; border: 1px solid transparent; background: transparent; }}
QToolButton:hover {{ background: #E5F1FB; border: 1px solid {SOFT_BORDER}; }}
QToolButton:pressed {{ background: {SELECTION}; border: 1px solid {BORDER}; }}
QToolButton:disabled {{ color: #9A9A9A; }}
QTableWidget {{
    background: {LIST}; border: 1px solid {BORDER}; gridline-color: #E4E4E4;
    selection-background-color: {SELECTION}; selection-color: {TEXT};
}}
QTableWidget::item {{ padding: 2px 4px; }}
QHeaderView::section {{
    background: {PANEL}; color: {TEXT}; padding: 3px 6px;
    border: none; border-right: 1px solid {SOFT_BORDER};
    border-bottom: 1px solid {BORDER};
}}
QFrame#pathBar {{ background: {PANEL}; border-top: 1px solid {BORDER}; }}
QLineEdit {{ background: {LIST}; border: 1px solid {BORDER}; padding: 3px 4px; }}
QLineEdit:disabled {{ background: {WINDOW}; color: {MUTED}; }}
QPushButton {{
    background: {PANEL}; border: 1px solid {BORDER}; padding: 3px 12px; min-height: 18px;
}}
QPushButton:hover {{ background: #E5F1FB; }}
QPushButton:pressed {{ background: {SELECTION}; }}
QPushButton:disabled {{ color: #9A9A9A; background: {WINDOW}; }}
QCheckBox {{ spacing: 6px; }}
QProgressBar {{
    border: 1px solid {BORDER}; background: {LIST}; text-align: center; max-height: 14px;
}}
QProgressBar::chunk {{ background: #4F94CD; }}
QStatusBar {{ background: {PANEL}; border-top: 1px solid {SOFT_BORDER}; }}
QStatusBar::item {{ border: none; }}
QLabel#statusPanel {{ border: 1px solid {SOFT_BORDER}; padding: 1px 6px; background: {PANEL}; }}
"""


def apply_theme(app: QApplication) -> None:
    """应用经典工具风格。"""
    app.setStyleSheet(STYLE_SHEET)


__all__ = ["ACCENT", "apply_theme"]
