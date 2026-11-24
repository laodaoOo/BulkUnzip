"""界面配色：Windows 11 浅色原生风格（白底、圆角、细分隔线、蓝色主按钮）。"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

BACKGROUND = "#F3F3F3"
SURFACE = "#FFFFFF"
HOVER = "#F7F7F7"
BORDER = "#E1E1E1"
CONTROL_BORDER = "#D6D6D6"
TEXT = "#1B1B1B"
MUTED = "#616161"
ACCENT = "#0067C0"
ACCENT_HOVER = "#1975C5"
ACCENT_PRESSED = "#005A9E"

STYLE_SHEET = f"""
QWidget {{
    color: {TEXT};
    font-family: "Segoe UI Variable Text", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
}}
QMainWindow, QWidget#root, QDialog {{ background: {BACKGROUND}; }}
QFrame#header {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}
QLabel#appName {{
    font-family: "Segoe UI Variable Display", "Microsoft YaHei UI", sans-serif;
    font-size: 22px; font-weight: 600;
}}
QLabel#subtitle, QLabel#muted {{ color: {MUTED}; }}
QLabel#sectionTitle {{ font-size: 15px; font-weight: 600; }}
QLabel#rowTitle {{ font-weight: 600; }}
QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; }}
QListWidget#taskList {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px;
    outline: none;
}}
QListWidget#taskList::item {{ border-radius: 6px; margin: 2px; }}
QListWidget#taskList::item:hover {{ background: {HOVER}; }}
QListWidget#taskList::item:selected {{ background: #E8F1FB; }}
QPushButton {{
    background: {SURFACE}; border: 1px solid {CONTROL_BORDER}; border-radius: 5px;
    padding: 6px 14px; min-height: 18px;
}}
QPushButton:hover {{ background: {HOVER}; }}
QPushButton:pressed {{ background: #EFEFEF; }}
QPushButton:disabled {{ color: #A0A0A0; background: #FAFAFA; border-color: #EBEBEB; }}
QPushButton#primary {{
    background: {ACCENT}; color: #FFFFFF; border: none; font-weight: 600;
    padding: 8px 18px;
}}
QPushButton#primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#primary:pressed {{ background: {ACCENT_PRESSED}; }}
QPushButton#primary:disabled {{ background: #C9C9C9; color: #FFFFFF; }}
QLineEdit {{
    background: {SURFACE}; border: 1px solid {CONTROL_BORDER}; border-radius: 5px;
    padding: 5px 8px;
}}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}
QLineEdit:disabled {{ background: #FAFAFA; color: #A0A0A0; }}
QCheckBox {{ spacing: 8px; }}
QProgressBar {{
    border: none; background: #E9E9E9; border-radius: 3px;
    min-height: 6px; max-height: 6px;
}}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #C9C9C9; border-radius: 5px; min-height: 24px; }}
QScrollBar::handle:vertical:hover {{ background: #A8A8A8; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
"""


def apply_theme(app: QApplication) -> None:
    """应用 Win11 浅色风格。"""
    app.setStyleSheet(STYLE_SHEET)


__all__ = ["ACCENT", "apply_theme"]
