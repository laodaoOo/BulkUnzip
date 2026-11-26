"""日志、结果与工具路径三个对话框。"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core import Outcome, find_tool
from gui.config import Settings


class LogDialog(QDialog):
    """任务日志。"""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("任务日志 · BulkUnzip")
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setMaximumBlockCount(3000)
        self.text.setPlaceholderText("开始解压后，这里显示处理过程。")
        layout.addWidget(self.text)

    def append(self, line: str) -> None:
        if line.strip():
            self.text.appendPlainText(line.strip())

    def clear(self) -> None:
        self.text.clear()


class ResultDialog(QDialog):
    """完成摘要：重命名与未解开的压缩包，可直接打开输出目录。"""

    def __init__(self, parent: QWidget | None, outcome: Outcome, output: Path) -> None:
        super().__init__(parent)
        self.setWindowTitle("解压结果 · BulkUnzip")
        self.resize(620, 460)
        self._output = output
        layout = QVBoxLayout(self)
        summary = QLabel(
            f"已解开 {outcome.archives} 个压缩包，写入 {outcome.entries} 个条目。"
            + (f" 已删除 {outcome.removed} 个源压缩包。" if outcome.removed else "")
        )
        summary.setObjectName("sectionTitle")
        summary.setWordWrap(True)
        layout.addWidget(summary)
        detail = QPlainTextEdit()
        detail.setReadOnly(True)
        lines: list[str] = []
        if outcome.renames:
            lines.append(f"重命名 {len(outcome.renames)} 项：")
            lines.extend(f"  {old}  →  {new}" for old, new in outcome.renames)
        if outcome.failures:
            lines.append(f"未解开 {len(outcome.failures)} 个：")
            lines.extend(f"  {name}：{reason}" for name, reason in outcome.failures)
        if not lines:
            lines.append("没有重命名，也没有失败。")
        detail.setPlainText("\n".join(lines))
        layout.addWidget(detail, 1)
        buttons = QHBoxLayout()
        open_button = QPushButton("打开输出目录")
        open_button.clicked.connect(self._open_output)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        buttons.addStretch(1)
        buttons.addWidget(open_button)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)

    def _open_output(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._output)))


class SettingsDialog(QDialog):
    """主题与工具路径设置。"""

    #: 主题选项：(设置值, 显示文字)。
    THEME_OPTIONS = (
        ("light", "浅色"),
        ("dark", "深色"),
        ("system", "使用系统设置"),
    )

    def __init__(self, parent: QWidget | None, settings: Settings) -> None:
        super().__init__(parent)
        self.setWindowTitle("设置 · BulkUnzip")
        self.resize(560, 420)
        self._settings = settings
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        theme_title = QLabel("应用主题")
        theme_title.setObjectName("rowTitle")
        layout.addWidget(theme_title)
        self._theme_buttons: dict[str, QRadioButton] = {}
        for value, text in self.THEME_OPTIONS:
            radio = QRadioButton(text)
            radio.setChecked(settings.theme == value)
            self._theme_buttons[value] = radio
            layout.addWidget(radio)
        if not any(radio.isChecked() for radio in self._theme_buttons.values()):
            self._theme_buttons["system"].setChecked(True)
        layout.addSpacing(6)
        hint = QLabel(
            "zip / 7z 需要 7-Zip 的 7z.exe，rar 需要 WinRAR 的 Rar.exe。"
            "留空时自动在程序目录、安装目录和 PATH 中查找。"
        )
        hint.setWordWrap(True)
        hint.setObjectName("muted")
        layout.addWidget(hint)
        self.sevenzip_edit = self._path_row(layout, "7-Zip", settings.sevenzip_path)
        self.rar_edit = self._path_row(layout, "WinRAR", settings.rar_path)
        layout.addStretch(1)
        buttons = QHBoxLayout()
        detect = QPushButton("自动检测")
        detect.clicked.connect(self._detect)
        cancel = QPushButton("取消")
        cancel.clicked.connect(self.reject)
        confirm = QPushButton("保存")
        confirm.setObjectName("primary")
        confirm.clicked.connect(self.accept)
        buttons.addWidget(detect)
        buttons.addStretch(1)
        buttons.addWidget(cancel)
        buttons.addWidget(confirm)
        layout.addLayout(buttons)

    def _path_row(self, layout: QVBoxLayout, title: str, value: str) -> QLineEdit:
        row = QHBoxLayout()
        label = QLabel(title)
        label.setFixedWidth(60)
        edit = QLineEdit(value)
        edit.setPlaceholderText("auto（留空自动查找）")
        browse = QPushButton("浏览…")
        browse.clicked.connect(lambda: self._browse(edit))
        row.addWidget(label)
        row.addWidget(edit, 1)
        row.addWidget(browse)
        layout.addLayout(row)
        return edit

    def _browse(self, edit: QLineEdit) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self, "选择命令行工具", "", "可执行文件 (*.exe);;所有文件 (*.*)",
        )
        if selected:
            edit.setText(selected)

    def _detect(self) -> None:
        sevenzip = find_tool("7z")
        rar = find_tool("rar")
        self.sevenzip_edit.setText(str(sevenzip) if sevenzip else "")
        self.rar_edit.setText(str(rar) if rar else "")

    def values(self) -> Settings:
        theme = next(
            (value for value, radio in self._theme_buttons.items() if radio.isChecked()),
            "system",
        )
        return Settings(
            output_directory=self._settings.output_directory,
            delete_source=self._settings.delete_source,
            sevenzip_path=self.sevenzip_edit.text().strip(),
            rar_path=self.rar_edit.text().strip(),
            theme=theme,
        )


__all__ = ["LogDialog", "ResultDialog", "SettingsDialog"]
