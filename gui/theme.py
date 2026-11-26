"""主题：浅色 / 深色 / 跟随系统，含调色板与 Windows 深色标题栏。"""

from __future__ import annotations

import ctypes
import sys
from string import Template

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette
from PySide6.QtWidgets import QApplication, QWidget

from gui.resources import asset_path

# 可选的主题设置。
THEME_MODES = ("light", "dark", "system")

LIGHT = {
    "background": "#F3F3F3",
    "surface": "#FFFFFF",
    "surface_alt": "#FAFAFA",
    "hover": "#F7F7F7",
    "pressed": "#EFEFEF",
    "stroke": "#E5E5E5",
    "control_stroke": "#D6D6D6",
    "text": "#1A1A1A",
    "text_secondary": "#5D5D5D",
    "text_tertiary": "#8A8A8A",
    "accent": "#0067C0",
    "on_accent": "#FFFFFF",
    "accent_hover": "#1975C5",
    "accent_pressed": "#005A9E",
    "success": "#0F7B0F",
    "warning": "#9D5D00",
    "danger": "#C42B1C",
    "selection": "#E8F1FB",
    "track": "#E9E9E9",
    "scroll": "#C9C9C9",
    "scroll_hover": "#A8A8A8",
    "disabled_text": "#A0A0A0",
    "disabled_bg": "#FAFAFA",
    "disabled_border": "#EBEBEB",
    "primary_disabled": "#C9C9C9",
    "check_border": "#8A8A8A",
}

DARK = {
    "background": "#202020",
    "surface": "#2B2B2B",
    "surface_alt": "#272727",
    "hover": "#333333",
    "pressed": "#3A3A3A",
    "stroke": "#3A3A3A",
    "control_stroke": "#4A4A4A",
    "text": "#F2F2F2",
    "text_secondary": "#C8C8C8",
    "text_tertiary": "#9A9A9A",
    "accent": "#4CC2FF",
    "on_accent": "#0B1B26",
    "accent_hover": "#5ACBFF",
    "accent_pressed": "#3AA9E0",
    "success": "#6CCB5F",
    "warning": "#FCE100",
    "danger": "#FF99A4",
    "selection": "#2D4A63",
    "track": "#3A3A3A",
    "scroll": "#5A5A5A",
    "scroll_hover": "#6E6E6E",
    "disabled_text": "#6E6E6E",
    "disabled_bg": "#262626",
    "disabled_border": "#333333",
    "primary_disabled": "#3A3A3A",
    "check_border": "#8A8A8A",
}

_TEMPLATE = Template("""
QWidget {
    color: $text;
    font-family: "Segoe UI Variable Text", "Microsoft YaHei UI", sans-serif;
    font-size: 13px;
}
QMainWindow, QWidget#root, QDialog { background: $background; }
QMessageBox { background: $surface; min-width: 380px; }
QMessageBox QLabel { font-size: 13px; }
QMessageBox QPushButton { min-width: 88px; }

QLabel#appName {
    font-family: "Segoe UI Variable Display", "Microsoft YaHei UI", sans-serif;
    font-size: 20px; font-weight: 600;
}
QLabel#subtitle { color: $text_secondary; font-size: 12px; }
QLabel#sectionTitle { font-size: 15px; font-weight: 600; }
QLabel#dialogTitle { font-size: 20px; font-weight: 600; }
QLabel#fieldLabel { color: $text_secondary; font-size: 12px; }
QLabel#caption, QLabel#muted { color: $text_secondary; font-size: 12px; }
QLabel#rowName { font-size: 13px; font-weight: 600; }
QLabel#rowState { color: $text_secondary; font-size: 12px; }

QFrame#panel { background: $surface; border: 1px solid $stroke; border-radius: 8px; }
QFrame#emptyState {
    background: $surface; border: 1px dashed $control_stroke; border-radius: 8px;
}
QFrame#separator { background: $stroke; min-height: 1px; max-height: 1px; border: none; }
QFrame#rowDivider { background: $stroke; min-height: 1px; max-height: 1px; border: none; }

QListWidget#taskList { background: transparent; border: none; outline: none; padding: 0; }
QListWidget#taskList::item { background: transparent; border: none; }
QWidget#taskRow { background: transparent; }
QWidget#taskRowContent:hover { background: $hover; }

QLabel#statusDot { border-radius: 4px; background: $text_tertiary; }
QLabel#statusDot[state="running"] { background: $accent; }
QLabel#statusDot[state="paused"] { background: $warning; }
QLabel#statusDot[state="done"] { background: $success; }
QLabel#statusDot[state="failed"] { background: $danger; }

QPushButton {
    background: $surface; border: 1px solid $control_stroke; border-radius: 4px;
    padding: 0 14px; min-height: 30px;
}
QPushButton:hover { background: $hover; }
QPushButton:pressed { background: $pressed; }
QPushButton:focus { border: 1px solid $accent; }
QPushButton:disabled {
    color: $disabled_text; background: $disabled_bg; border-color: $disabled_border;
}
QPushButton#primary {
    background: $accent; color: $on_accent; border: 1px solid transparent;
    font-weight: 600; min-height: 34px; padding: 0 18px;
}
QPushButton#primary:hover { background: $accent_hover; }
QPushButton#primary:pressed { background: $accent_pressed; }
QPushButton#primary:focus { border: 2px solid $on_accent; }
QPushButton#primary:disabled { background: $primary_disabled; color: $disabled_text; }
QPushButton#danger {
    background: $surface; border: 1px solid $control_stroke; color: $danger;
}
QPushButton#danger:hover { background: $hover; border-color: $danger; }
QPushButton#danger:pressed { background: $pressed; }
QPushButton#danger:focus { border: 2px solid $accent; }
QToolButton { background: transparent; border: none; border-radius: 4px; }
QToolButton:hover { background: $hover; }
QToolButton:pressed { background: $pressed; }

QLineEdit {
    background: $surface; border: 1px solid $control_stroke; border-radius: 4px;
    padding: 0 10px; min-height: 30px;
    selection-background-color: $accent; selection-color: $on_accent;
}
QLineEdit:focus { border: 1px solid $accent; }
QLineEdit:disabled { background: $disabled_bg; color: $disabled_text; }

QPlainTextEdit {
    background: $surface_alt; color: $text; border: 1px solid $stroke;
    border-radius: 4px; padding: 10px;
    selection-background-color: $accent; selection-color: $on_accent;
}

QCheckBox, QRadioButton { spacing: 8px; }
QCheckBox { padding: 2px 0; min-height: 22px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 3px;
    border: 1px solid $check_border; background: $surface;
}
QCheckBox::indicator:hover { border-color: $accent; }
QCheckBox::indicator:checked {
    background: $accent; border-color: $accent; image: url("$check");
}

QProgressBar {
    border: none; background: $track; border-radius: 3px;
    min-height: 6px; max-height: 6px;
}
QProgressBar::chunk { background: $accent; border-radius: 3px; }

QMenu { background: $surface; border: 1px solid $stroke; padding: 4px; }
QMenu::item { padding: 5px 22px 5px 14px; border-radius: 4px; }
QMenu::item:selected { background: $selection; }
QMenu::separator { height: 1px; background: $stroke; margin: 4px 8px; }
QToolTip { background: $surface; color: $text; border: 1px solid $stroke; padding: 4px 6px; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 2px; }
QScrollBar::handle:vertical { background: $scroll; border-radius: 5px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: $scroll_hover; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
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
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(table["text_tertiary"]))
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
    table = dict(DARK if resolved == "dark" else LIGHT)
    table["check"] = asset_path("check.png").as_posix()
    setter = getattr(app.styleHints(), "setColorScheme", None)
    if setter is not None:
        try:
            setter(Qt.ColorScheme.Dark if resolved == "dark" else Qt.ColorScheme.Light)
        except (TypeError, AttributeError):
            pass
    app.setPalette(build_palette(table))
    _apply_fluent_theme(resolved)
    app.setStyleSheet(_TEMPLATE.substitute(**table))
    return resolved


def _apply_fluent_theme(resolved: str) -> None:
    """让 Fluent 列表与图标跟随深浅色。"""
    from qfluentwidgets import Theme, setTheme

    setTheme(Theme.DARK if resolved == "dark" else Theme.LIGHT)


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
