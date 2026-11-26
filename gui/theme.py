"""主题：浅色 / 深色 / 跟随系统，含调色板与 Windows 深色标题栏。"""

from __future__ import annotations

import ctypes
import sys
from string import Template

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication, QWidget

# 可选的主题设置。
THEME_MODES = ("light", "dark", "system")

LIGHT = {
    "background": "#F3F3F3",
    "surface": "#FFFFFF",
    "hover": "#F7F7F7",
    "pressed": "#EFEFEF",
    "border": "#E1E1E1",
    "control_border": "#D6D6D6",
    "text": "#1B1B1B",
    "muted": "#616161",
    "accent": "#0067C0",
    "on_accent": "#FFFFFF",
    "accent_hover": "#1975C5",
    "accent_pressed": "#005A9E",
    "selection": "#E8F1FB",
    "track": "#E9E9E9",
    "scroll": "#C9C9C9",
    "scroll_hover": "#A8A8A8",
    "disabled_text": "#A0A0A0",
    "disabled_bg": "#FAFAFA",
    "disabled_border": "#EBEBEB",
    "primary_disabled": "#C9C9C9",
}

DARK = {
    "background": "#202020",
    "surface": "#2B2B2B",
    "hover": "#333333",
    "pressed": "#3A3A3A",
    "border": "#3A3A3A",
    "control_border": "#4A4A4A",
    "text": "#F2F2F2",
    "muted": "#A8A8A8",
    "accent": "#4CC2FF",
    "on_accent": "#0B1B26",
    "accent_hover": "#5ACBFF",
    "accent_pressed": "#3AA9E0",
    "selection": "#2D4A63",
    "track": "#3A3A3A",
    "scroll": "#5A5A5A",
    "scroll_hover": "#6E6E6E",
    "disabled_text": "#6E6E6E",
    "disabled_bg": "#262626",
    "disabled_border": "#333333",
    "primary_disabled": "#3A3A3A",
}

_TEMPLATE = Template("""
QWidget {
    color: $text;
    font-family: "Segoe UI Variable Text", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
}
QMainWindow, QWidget#root, QDialog, QMessageBox { background: $background; }
QFrame#header { background: $surface; border-bottom: 1px solid $border; }
QLabel#appName {
    font-family: "Segoe UI Variable Display", "Microsoft YaHei UI", sans-serif;
    font-size: 22px; font-weight: 600;
}
QLabel#subtitle, QLabel#muted { color: $muted; }
QLabel#sectionTitle { font-size: 15px; font-weight: 600; }
QLabel#rowTitle { font-weight: 600; }
QFrame#card { background: $surface; border: 1px solid $border; border-radius: 8px; }
QListWidget#taskList {
    background: $surface; border: 1px solid $border; border-radius: 8px;
    padding: 4px; outline: none;
}
QListWidget#taskList::item { border-radius: 6px; margin: 2px; }
QListWidget#taskList::item:hover { background: $hover; }
QListWidget#taskList::item:selected { background: $selection; }
QPushButton {
    background: $surface; border: 1px solid $control_border; border-radius: 5px;
    padding: 6px 14px; min-height: 18px;
}
QPushButton:hover { background: $hover; }
QPushButton:pressed { background: $pressed; }
QPushButton:disabled {
    color: $disabled_text; background: $disabled_bg; border-color: $disabled_border;
}
QPushButton#primary {
    background: $accent; color: $on_accent; border: none; font-weight: 600;
    padding: 8px 18px;
}
QPushButton#primary:hover { background: $accent_hover; }
QPushButton#primary:pressed { background: $accent_pressed; }
QPushButton#primary:disabled { background: $primary_disabled; color: $disabled_text; }
QLineEdit {
    background: $surface; border: 1px solid $control_border; border-radius: 5px;
    padding: 5px 8px; selection-background-color: $accent; selection-color: $on_accent;
}
QLineEdit:focus { border: 1px solid $accent; }
QLineEdit:disabled { background: $disabled_bg; color: $disabled_text; }
QPlainTextEdit {
    background: $surface; color: $text; border: 1px solid $border;
    border-radius: 6px; selection-background-color: $accent; selection-color: $on_accent;
}
QCheckBox, QRadioButton { spacing: 8px; }
QProgressBar {
    border: none; background: $track; border-radius: 3px;
    min-height: 6px; max-height: 6px;
}
QProgressBar::chunk { background: $accent; border-radius: 3px; }
QMenu { background: $surface; border: 1px solid $border; padding: 4px; }
QMenu::item { padding: 5px 22px 5px 14px; border-radius: 4px; }
QMenu::item:selected { background: $selection; }
QMenu::separator { height: 1px; background: $border; margin: 4px 8px; }
QToolTip { background: $surface; color: $text; border: 1px solid $border; padding: 4px 6px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $scroll; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: $scroll_hover; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QStatusBar { background: $surface; border-top: 1px solid $border; }
""")

# Windows 深色标题栏的属性号（20 适用于 Win10 20H1+，19 为旧版本）。
_DWMWA_DARK_MODE = 20
_DWMWA_DARK_MODE_LEGACY = 19


def system_mode() -> str:
    """读取系统当前的深浅色。"""
    hints = QGuiApplication.styleHints()
    scheme = hints.colorScheme()
    return "dark" if scheme == Qt.ColorScheme.Dark else "light"


def resolve_mode(mode: str) -> str:
    """把设置里的 light / dark / system 解析成实际的深浅色。"""
    if mode in ("light", "dark"):
        return mode
    return system_mode()


def build_palette(table: dict[str, str]) -> QPalette:
    """按主题生成调色板，覆盖未单独写样式的控件。"""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(table["background"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(table["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(table["surface"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(table["hover"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(table["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(table["surface"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(table["text"]))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(table["accent"]))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(table["surface"]))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(table["text"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(table["accent"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(table["on_accent"]))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(table["muted"]))
    palette.setColor(QPalette.ColorRole.Link, QColor(table["accent"]))
    for role in (
        QPalette.ColorRole.Text,
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, QColor(table["disabled_text"]))
    return palette


def apply_theme(app: QApplication, mode: str) -> str:
    """应用主题，返回实际使用的 light / dark。"""
    resolved = resolve_mode(mode)
    table = DARK if resolved == "dark" else LIGHT
    setter = getattr(app.styleHints(), "setColorScheme", None)
    if setter is not None:
        try:
            setter(Qt.ColorScheme.Dark if resolved == "dark" else Qt.ColorScheme.Light)
        except (TypeError, AttributeError):
            pass
    app.setPalette(build_palette(table))
    app.setStyleSheet(_TEMPLATE.substitute(**table))
    return resolved


def apply_title_bar(window: QWidget, dark: bool) -> None:
    """Windows 下把窗口标题栏切成深色或浅色。"""
    if sys.platform != "win32":
        return
    try:
        hwnd = int(window.winId())
        value = ctypes.c_int(1 if dark else 0)
        for attribute in (_DWMWA_DARK_MODE, _DWMWA_DARK_MODE_LEGACY):
            result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, attribute, ctypes.byref(value), ctypes.sizeof(value),
            )
            if result == 0:
                return
    except Exception:  # noqa: BLE001 - 非 Windows 或旧系统上失败可忽略
        return


__all__ = [
    "THEME_MODES",
    "apply_theme",
    "apply_title_bar",
    "resolve_mode",
]
