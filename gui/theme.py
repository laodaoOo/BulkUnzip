"""界面配色：与 NestPack 同一套紫色 Fluent 观感。"""

from __future__ import annotations

from PySide6.QtWidgets import QApplication

ACCENT = "#725196"
PANEL = "#F0EAF7"
BORDER = "#DAD2E6"
TEXT = "#2D3249"
MUTED = "#716A80"
BACKGROUND = "#FCFAFE"

STYLE_SHEET = f"""
QWidget {{ color: {TEXT}; font-family: "Microsoft YaHei UI"; font-size: 13px; }}
QMainWindow, QWidget#root {{ background: {BACKGROUND}; }}
QFrame#header {{ background: #FFFFFF; border-bottom: 1px solid {BORDER}; }}
QLabel#appName {{ font-family: "Trebuchet MS"; font-size: 24px; font-weight: 700; }}
QLabel#subtitle, QLabel#muted {{ color: {MUTED}; }}
QLabel#sectionTitle {{ font-size: 16px; font-weight: 600; }}
QListWidget#taskList {{
    background: #FFFFFF; border: 1px solid #B8A4D1; border-radius: 8px;
}}
QListWidget#taskList::item {{ border-bottom: 1px solid #EFE9F6; }}
QPushButton {{
    border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 14px; background: #FFFFFF;
}}
QPushButton:hover {{ background: {PANEL}; }}
QPushButton#primary {{
    background: {ACCENT}; color: #FFFFFF; border: none; font-weight: 600; padding: 11px 18px;
}}
QPushButton#primary:hover {{ background: #5F4380; }}
QPushButton#primary:disabled {{ background: #C9BBD9; }}
QProgressBar {{
    border: none; background: #E4DBEF; border-radius: 4px;
    min-height: 8px; max-height: 8px;
}}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 4px; }}
QLineEdit {{
    border: 1px solid {BORDER}; border-radius: 6px; padding: 8px; background: #FFFFFF;
}}
QCheckBox {{ spacing: 8px; }}
"""


def apply_theme(app: QApplication) -> None:
    """应用统一配色。"""
    app.setStyleSheet(STYLE_SHEET)


__all__ = ["ACCENT", "apply_theme"]
