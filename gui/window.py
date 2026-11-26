"""主窗口：拖入 1 级目录，逐行解压到输出目录（Windows 11 浅色风格）。"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core import Outcome, SourcePlan, plan_sources, resolve_tool
from gui.config import Settings, load_settings, save_settings
from gui.dialogs import LogDialog, ResultDialog, SettingsDialog
from gui.resources import asset_path
from gui.tasks import ExtractWorker
from gui.theme import apply_theme, apply_title_bar

ROW_HEIGHT = 68


class TaskRow(QWidget):
    """一行任务：目录名、状态、进度与移除。"""

    def __init__(self, path: Path, on_remove) -> None:
        super().__init__()
        self.path = path
        self._done = 0
        self._total = 1
        self._percent = 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 6, 6)
        layout.setSpacing(12)
        text = QVBoxLayout()
        text.setSpacing(2)
        name = QLabel(path.name)
        name.setObjectName("rowTitle")
        self.status = QLabel("等待开始")
        self.status.setObjectName("muted")
        text.addWidget(name)
        text.addWidget(self.status)
        layout.addLayout(text, 1)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedWidth(150)
        layout.addWidget(self.progress)
        remove = QPushButton("移除")
        remove.setFixedWidth(64)
        remove.clicked.connect(on_remove)
        layout.addWidget(remove)

    def waiting(self) -> None:
        """回到等待状态。"""
        self._done = 0
        self._total = 1
        self._percent = 0
        self.status.setText("等待开始")
        self.progress.setValue(0)

    def running(self, total: int) -> None:
        """开始解压这个目录。"""
        self._done = 0
        self._total = max(total, 1)
        self._percent = 0
        self.status.setText(f"解压中 0/{self._total}")
        self.progress.setValue(0)

    def set_count(self, done: int, total: int) -> None:
        """更新已完成的压缩包个数。"""
        self._done = done
        self._total = max(total, 1)
        self.status.setText(f"解压中 {self._done}/{self._total} · {self._percent}%")

    def set_percent(self, value: int) -> None:
        """更新当前压缩包的实时百分比。"""
        self._percent = value
        self.progress.setValue(value)
        self.status.setText(f"解压中 {self._done}/{self._total} · {value}%")

    def finished(self, outcome: Outcome) -> None:
        """显示完成统计。"""
        if outcome.skipped:
            self.status.setText("没有找到压缩包")
            self.progress.setValue(0)
            return
        text = f"完成 {outcome.archives} 个包 / {outcome.entries} 个条目"
        if outcome.removed:
            text += f"，已删源 {outcome.removed}"
        if outcome.failures:
            text += f"，失败 {len(outcome.failures)}"
        self.status.setText(text)
        self.progress.setValue(100)

    def cancelled(self) -> None:
        """取消后的状态。"""
        self.status.setText("已停止")


class MainWindow(QMainWindow):
    """拖入即任务列表；一次执行一个目录，结束再下一个。"""

    def __init__(self) -> None:
        super().__init__()
        self.settings: Settings = load_settings()
        self._rows: list[TaskRow] = []
        self._plans: list[SourcePlan] = []
        self._worker: ExtractWorker | None = None
        self._tools: dict[str, Path | None] = {"7z": None, "rar": None}
        self._error = ""
        self._cancel_requested = False
        self._resolved_theme = apply_theme(QApplication.instance(), self.settings.theme)
        hints = QGuiApplication.styleHints()
        scheme_changed = getattr(hints, "colorSchemeChanged", None)
        if scheme_changed is not None:
            scheme_changed.connect(self._system_theme_changed)
        self.setWindowTitle("BulkUnzip")
        self.setWindowIcon(QIcon(str(asset_path("app.ico"))))
        self.resize(960, 640)
        self.setMinimumSize(760, 520)
        self.setAcceptDrops(True)
        self._build_ui()
        self.log_dialog = LogDialog(self)
        self._restore()

    # ---------- 界面 ----------

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_header())
        layout.addWidget(self._build_body(), 1)

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        row = QHBoxLayout(header)
        row.setContentsMargins(20, 12, 20, 12)
        row.setSpacing(14)
        title = QLabel("BulkUnzip")
        title.setObjectName("appName")
        row.addWidget(title)
        subtitle = QLabel("批量解压 · 1 级 / 2 级目录")
        subtitle.setObjectName("subtitle")
        row.addWidget(subtitle)
        row.addStretch(1)
        self.tool_label = QLabel("正在检测工具…")
        self.tool_label.setObjectName("muted")
        row.addWidget(self.tool_label)
        settings_button = QPushButton("设置")
        settings_button.clicked.connect(self._open_settings)
        row.addWidget(settings_button)
        return header

    def _build_body(self) -> QWidget:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)
        top = QHBoxLayout()
        top.setSpacing(8)
        section = QLabel("任务")
        section.setObjectName("sectionTitle")
        top.addWidget(section)
        top.addStretch(1)
        add_button = QPushButton("添加目录")
        add_button.clicked.connect(self._choose_sources)
        clear_button = QPushButton("清空")
        clear_button.clicked.connect(self._clear)
        top.addWidget(add_button)
        top.addWidget(clear_button)
        layout.addLayout(top)
        self.empty_hint = QLabel("把 1 级目录拖到这里，或点「添加目录」")
        self.empty_hint.setObjectName("muted")
        self.empty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.empty_hint)
        self.list = QListWidget()
        self.list.setObjectName("taskList")
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.itemDoubleClicked.connect(self._open_row_output)
        layout.addWidget(self.list, 1)
        layout.addWidget(self._build_card())
        return body

    def _build_card(self) -> QWidget:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        output_row = QHBoxLayout()
        output_row.setSpacing(8)
        label = QLabel("输出目录")
        label.setObjectName("muted")
        label.setFixedWidth(60)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("解压结果写到这个目录")
        self.output_edit.textChanged.connect(self._output_changed)
        browse = QPushButton("浏览")
        browse.setFixedWidth(64)
        browse.clicked.connect(self._choose_output)
        output_row.addWidget(label)
        output_row.addWidget(self.output_edit, 1)
        output_row.addWidget(browse)
        layout.addLayout(output_row)
        self.delete_check = QCheckBox("解压后删除源文件（每个 2 级目录解开后清理）")
        self.delete_check.toggled.connect(self._delete_changed)
        layout.addWidget(self.delete_check)
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.start_button = QPushButton("开始解压")
        self.start_button.setObjectName("primary")
        self.start_button.setMinimumHeight(34)
        self.start_button.clicked.connect(self._start)
        self.cancel_button = QPushButton("停止")
        self.cancel_button.clicked.connect(self._cancel)
        self.cancel_button.hide()
        log_button = QPushButton("查看日志")
        log_button.clicked.connect(self._show_log)
        open_button = QPushButton("打开输出目录")
        open_button.clicked.connect(self._open_output)
        actions.addWidget(self.start_button, 1)
        actions.addWidget(self.cancel_button)
        actions.addWidget(log_button)
        actions.addWidget(open_button)
        layout.addLayout(actions)
        self.summary = QLabel("")
        self.summary.setObjectName("muted")
        layout.addWidget(self.summary)
        return card

    # ---------- 状态 ----------

    def _restore(self) -> None:
        """恢复上次设置，并接收命令行/拖到 exe 上的目录。"""
        if self.settings.output_directory:
            self.output_edit.setText(self.settings.output_directory)
        self.delete_check.setChecked(self.settings.delete_source)
        self._refresh_tools()
        self.add_paths([Path(item) for item in sys.argv[1:]])
        self._refresh_summary()

    def _refresh_tools(self) -> None:
        """解析工具路径并显示状态。"""
        for kind, key in (("7z", "sevenzip_path"), ("rar", "rar_path")):
            try:
                self._tools[kind] = resolve_tool(kind, getattr(self.settings, key))
            except ValueError as error:
                self._tools[kind] = None
                self.summary.setText(str(error))
        self.tool_label.setText(
            f"7-Zip {'已就绪' if self._tools['7z'] else '未找到'}　"
            f"WinRAR {'已就绪' if self._tools['rar'] else '未找到'}",
        )

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.settings = dialog.values()
        save_settings(self.settings)
        self._apply_theme()
        self._refresh_tools()

    def _apply_theme(self) -> None:
        """按当前设置重新应用主题与标题栏。"""
        self._resolved_theme = apply_theme(QApplication.instance(), self.settings.theme)
        apply_title_bar(self, self._resolved_theme == "dark")

    def _system_theme_changed(self, _scheme: object) -> None:
        """系统深浅色变化时，跟随模式要立刻刷新。"""
        if self.settings.theme == "system":
            self._apply_theme()

    def _refresh_summary(self) -> None:
        count = len(self._rows)
        self.empty_hint.setVisible(count == 0)
        self.list.setVisible(count > 0)
        self.summary.setText(f"{count} 个任务" if count else "还没有任务")

    def _output_changed(self, text: str) -> None:
        self.settings.output_directory = text.strip()

    def _delete_changed(self, checked: bool) -> None:
        self.settings.delete_source = checked

    # ---------- 任务列表 ----------

    def add_paths(self, paths: list[Path]) -> bool:
        """添加目录任务，重复路径只保留一次，返回是否有变化。"""
        existing = {row.path.resolve() for row in self._rows}
        added = False
        for path in paths:
            if not path.is_dir():
                continue
            resolved = path.resolve()
            if resolved in existing:
                continue
            existing.add(resolved)
            self._append_row(Path(path))
            added = True
        self._refresh_summary()
        return added

    def _append_row(self, path: Path) -> None:
        item = QListWidgetItem()
        item.setSizeHint(QSize(0, ROW_HEIGHT))
        self.list.addItem(item)
        row = TaskRow(path, lambda: self._remove_row(item))
        self.list.setItemWidget(item, row)
        self._rows.append(row)

    def _remove_row(self, item: QListWidgetItem) -> None:
        row = self.list.itemWidget(item)
        index = self.list.row(item)
        if index < 0:
            return
        self.list.takeItem(index)
        if isinstance(row, TaskRow):
            self._rows = [entry for entry in self._rows if entry is not row]
        self._refresh_summary()

    def _choose_sources(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "选择 1 级目录")
        if selected:
            self.add_paths([Path(selected)])

    def _clear(self) -> None:
        if self._worker is not None:
            return
        self.list.clear()
        self._rows.clear()
        self._refresh_summary()

    def _choose_output(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self, "选择输出目录", self.output_edit.text().strip(),
        )
        if selected:
            self.output_edit.setText(selected)

    def _show_log(self) -> None:
        self.log_dialog.show()
        self.log_dialog.raise_()
        self.log_dialog.activateWindow()

    # ---------- 执行 ----------

    def _start(self) -> None:
        if self._worker is not None:
            return
        if not self._rows:
            QMessageBox.information(self, "还没有任务", "先把 1 级目录拖进来。")
            return
        output_text = self.output_edit.text().strip()
        if not output_text:
            QMessageBox.information(self, "缺少输出目录", "请先选择解压输出目录。")
            return
        output = Path(output_text)
        plans = plan_sources([row.path for row in self._rows], output)
        formats = {job.archive_format for plan in plans for job in plan.jobs}
        if not formats:
            QMessageBox.information(self, "没有压缩包", "所选目录里没有找到可解压的压缩包。")
            return
        missing = []
        if formats & {"zip", "7z"} and self._tools.get("7z") is None:
            missing.append("7-Zip（7z.exe）")
        if "rar" in formats and self._tools.get("rar") is None:
            missing.append("WinRAR（Rar.exe）")
        if missing:
            QMessageBox.warning(
                self, "缺少解压工具",
                "需要：" + "、".join(missing) + "。\n请在「设置」里指定路径或安装后重试。",
            )
            return
        self._plans = plans
        self.settings.output_directory = output_text
        self.settings.delete_source = self.delete_check.isChecked()
        save_settings(self.settings)
        self.log_dialog.clear()
        self._error = ""
        self._cancel_requested = False
        for row, plan in zip(self._rows, plans, strict=False):
            row.waiting()
            if plan.jobs:
                row.running(len(plan.jobs))
        self._set_running(True)
        worker = ExtractWorker(
            plans, output, dict(self._tools), self.delete_check.isChecked(), self,
        )
        worker.log.connect(self.log_dialog.append)
        worker.row_progress.connect(self._row_progress)
        worker.row_percent.connect(self._row_percent)
        worker.row_finished.connect(self._row_finished)
        worker.finished_all.connect(self._finished)
        worker.failed.connect(self._worker_failed)
        worker.finished.connect(self._worker_released)
        self._worker = worker
        worker.start()

    def _cancel(self) -> None:
        if self._worker is not None:
            self._cancel_requested = True
            self.cancel_button.setEnabled(False)
            self.summary.setText("正在停止…")
            self._worker.cancel()

    def _row_progress(self, index: int, done: int, total: int) -> None:
        if 0 <= index < len(self._rows):
            self._rows[index].set_count(done, total)

    def _row_percent(self, index: int, value: int) -> None:
        if 0 <= index < len(self._rows):
            self._rows[index].set_percent(value)

    def _row_finished(self, index: int, outcome: Outcome) -> None:
        if 0 <= index < len(self._rows):
            self._rows[index].finished(outcome)

    def _worker_failed(self, message: str) -> None:
        self._error = message

    def _finished(self, total: Outcome) -> None:
        self._set_running(False)
        if self._cancel_requested:
            for row in self._rows:
                if row.status.text().startswith("解压中"):
                    row.cancelled()
            self.summary.setText("已停止")
            return
        if self._error:
            self.summary.setText(f"失败：{self._error}")
            QMessageBox.critical(self, "解压失败", self._error)
            return
        parts = [f"完成 {total.archives} 个包", f"{total.entries} 个条目"]
        if total.removed:
            parts.append(f"已删源 {total.removed}")
        if total.renames:
            parts.append(f"重命名 {len(total.renames)}")
        if total.failures:
            parts.append(f"失败 {len(total.failures)}")
        self.summary.setText(" · ".join(parts))
        if total.renames or total.failures:
            ResultDialog(self, total, Path(self.output_edit.text().strip())).exec()

    def _worker_released(self) -> None:
        self._worker = None

    def _set_running(self, running: bool) -> None:
        for row in self._rows:
            row.setEnabled(not running)
        self.list.setEnabled(not running)
        self.output_edit.setEnabled(not running)
        self.delete_check.setEnabled(not running)
        self.start_button.setVisible(not running)
        self.cancel_button.setVisible(running)
        self.cancel_button.setEnabled(True)
        if not running:
            self.start_button.setEnabled(True)

    def _open_output(self) -> None:
        text = self.output_edit.text().strip()
        if text:
            QDesktopServices.openUrl(QUrl.fromLocalFile(text))

    def _open_row_output(self, item: QListWidgetItem) -> None:
        row = self.list.itemWidget(item)
        base = self.output_edit.text().strip()
        if isinstance(row, TaskRow) and base:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(base) / row.path.name)))

    # ---------- 拖放 ----------

    def _has_local_urls(self, event) -> bool:
        mime = event.mimeData()
        return mime.hasUrls() and any(url.isLocalFile() for url in mime.urls())

    def dragEnterEvent(self, event) -> None:
        if self._has_local_urls(event) and self._worker is None:
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:
        if self._has_local_urls(event) and self._worker is None:
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:
        if not self._has_local_urls(event) or self._worker is not None:
            super().dropEvent(event)
            return
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
        self.add_paths(paths)
        event.acceptProposedAction()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        apply_title_bar(self, self._resolved_theme == "dark")

    def closeEvent(self, event) -> None:
        if self._worker is not None:
            answer = QMessageBox.question(
                self, "任务正在运行", "是否停止当前任务并退出？",
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self._worker.cancel()
            self._worker.wait(5000)
        save_settings(self.settings)
        event.accept()


__all__ = ["MainWindow"]
