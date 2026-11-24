"""主窗口：7-Zip 风格的工具条 + 列表 + 路径栏 + 状态栏。"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from core import Outcome, SourcePlan, plan_sources, resolve_tool
from gui.config import Settings, load_settings, save_settings
from gui.dialogs import LogDialog, ResultDialog, SettingsDialog
from gui.resources import asset_path
from gui.tasks import ExtractWorker
from gui.version import APP_VERSION

COLUMNS = ("名称", "状态", "进度", "输出")
ROW_HEIGHT = 24
TOOLBAR_ICON = 24


@dataclass
class TaskEntry:
    """表格中的一行：来源目录与对应控件。"""

    path: Path
    status: QTableWidgetItem
    progress: QProgressBar
    target: QTableWidgetItem


class MainWindow(QMainWindow):
    """拖入 1 级目录，逐行解压；关闭前确认运行中的任务。"""

    def __init__(self) -> None:
        super().__init__()
        self.settings: Settings = load_settings()
        self._entries: list[TaskEntry] = []
        self._plans: list[SourcePlan] = []
        self._worker: ExtractWorker | None = None
        self._tools: dict[str, Path | None] = {"7z": None, "rar": None}
        self._error = ""
        self._cancel_requested = False
        self.setWindowTitle("BulkUnzip")
        self.setWindowIcon(QIcon(str(asset_path("app.ico"))))
        self.resize(960, 620)
        self.setMinimumSize(760, 480)
        self.setAcceptDrops(True)
        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self._build_table()
        self._build_layout()
        self._build_statusbar()
        self.log_dialog = LogDialog(self)
        self._restore()

    # ---------- 界面 ----------

    def _icon(self, pixmap: QStyle.StandardPixmap) -> QIcon:
        return self.style().standardIcon(pixmap)

    def _build_actions(self) -> None:
        self.add_action = QAction(
            self._icon(QStyle.StandardPixmap.SP_DirOpenIcon), "添加目录", self,
        )
        self.add_action.setShortcut(QKeySequence.StandardKey.Open)
        self.add_action.setStatusTip("把一个或多个 1 级目录加入任务列表")
        self.add_action.triggered.connect(self._choose_sources)
        self.remove_action = QAction(self._icon(QStyle.StandardPixmap.SP_TrashIcon), "移除", self)
        self.remove_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.remove_action.setStatusTip("移除选中的任务")
        self.remove_action.triggered.connect(self._remove_selected)
        self.clear_action = QAction(
            self._icon(QStyle.StandardPixmap.SP_DialogResetButton), "清空列表", self,
        )
        self.clear_action.triggered.connect(self._clear)
        self.start_action = QAction(
            self._icon(QStyle.StandardPixmap.SP_MediaPlay), "开始解压", self,
        )
        self.start_action.setStatusTip("按列表顺序逐个目录解压")
        self.start_action.triggered.connect(self._start)
        self.stop_action = QAction(self._icon(QStyle.StandardPixmap.SP_MediaStop), "停止", self)
        self.stop_action.setEnabled(False)
        self.stop_action.triggered.connect(self._cancel)
        self.log_action = QAction(
            self._icon(QStyle.StandardPixmap.SP_FileDialogDetailedView), "日志", self,
        )
        self.log_action.triggered.connect(self._show_log)
        self.settings_action = QAction(
            self._icon(QStyle.StandardPixmap.SP_FileDialogInfoView), "设置", self,
        )
        self.settings_action.triggered.connect(self._open_settings)
        self.detect_action = QAction("重新检测工具", self)
        self.detect_action.triggered.connect(self._refresh_tools)
        self.about_action = QAction("关于 BulkUnzip", self)
        self.about_action.triggered.connect(self._show_about)

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("文件(&F)")
        file_menu.addAction(self.add_action)
        file_menu.addSeparator()
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        edit_menu = self.menuBar().addMenu("编辑(&E)")
        edit_menu.addAction(self.remove_action)
        edit_menu.addAction(self.clear_action)
        tools_menu = self.menuBar().addMenu("工具(&T)")
        tools_menu.addAction(self.detect_action)
        tools_menu.addAction(self.settings_action)
        help_menu = self.menuBar().addMenu("帮助(&H)")
        help_menu.addAction(self.about_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("工具栏", self)
        toolbar.setObjectName("mainToolBar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setIconSize(QSize(TOOLBAR_ICON, TOOLBAR_ICON))
        for action in (self.add_action, self.remove_action, self.clear_action):
            toolbar.addAction(action)
        toolbar.addSeparator()
        toolbar.addAction(self.start_action)
        toolbar.addAction(self.stop_action)
        toolbar.addSeparator()
        toolbar.addAction(self.log_action)
        toolbar.addAction(self.settings_action)
        self.addToolBar(toolbar)

    def _build_table(self) -> None:
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(ROW_HEIGHT)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(True)
        self.table.setAcceptDrops(False)
        self.table.setSortingEnabled(False)
        self.table.itemDoubleClicked.connect(self._open_row_output)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(1, 230)
        self.table.setColumnWidth(2, 130)

    def _build_layout(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        layout.setContentsMargins(4, 4, 4, 0)
        layout.setSpacing(4)
        layout.addWidget(self.table, 1)
        layout.addWidget(self._build_path_bar())

    def _build_path_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("pathBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        label = QLabel("解压到:")
        layout.addWidget(label)
        self.output_edit = QLineEdit()
        self.output_edit.setPlaceholderText("选择解压输出目录")
        self.output_edit.textChanged.connect(self._output_changed)
        layout.addWidget(self.output_edit, 1)
        browse = QPushButton("浏览")
        browse.setFixedWidth(56)
        browse.setToolTip("浏览输出目录")
        browse.clicked.connect(self._choose_output)
        layout.addWidget(browse)
        self.delete_check = QCheckBox("解压后删除源文件")
        self.delete_check.setToolTip("一个 2 级目录的压缩包全部解开后才删除源文件")
        self.delete_check.toggled.connect(self._delete_changed)
        layout.addWidget(self.delete_check)
        return bar

    def _build_statusbar(self) -> None:
        self.summary = QLabel("0 个任务")
        self.statusBar().addWidget(self.summary, 1)
        self.tool_label = QLabel()
        self.tool_label.setObjectName("statusPanel")
        self.statusBar().addPermanentWidget(self.tool_label)

    def _show_about(self) -> None:
        QMessageBox.about(
            self, "关于 BulkUnzip",
            f"<b>BulkUnzip {APP_VERSION}</b><br>"
            "按 1 级 / 2 级目录批量解压（zip / 7z / rar）。<br><br>"
            "需要系统安装 7-Zip 与 WinRAR 命令行工具。<br>"
            "GPL-3.0-only，解压引擎源自 NestPack。",
        )

    # ---------- 状态 ----------

    def _restore(self) -> None:
        if self.settings.output_directory:
            self.output_edit.setText(self.settings.output_directory)
        self.delete_check.setChecked(self.settings.delete_source)
        self._refresh_tools()
        self.add_paths([Path(item) for item in sys.argv[1:]])
        self._refresh_summary()

    def _refresh_tools(self) -> None:
        for kind, key in (("7z", "sevenzip_path"), ("rar", "rar_path")):
            try:
                self._tools[kind] = resolve_tool(kind, getattr(self.settings, key))
            except ValueError:
                self._tools[kind] = None
        self.tool_label.setText(
            f"7-Zip {'✓' if self._tools['7z'] else '✗'}   "
            f"WinRAR {'✓' if self._tools['rar'] else '✗'}",
        )

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self.settings = dialog.values()
        save_settings(self.settings)
        self._refresh_tools()

    def _refresh_summary(self) -> None:
        self.summary.setText(f"{len(self._entries)} 个任务")

    def _output_changed(self, text: str) -> None:
        self.settings.output_directory = text.strip()
        self._refresh_targets()

    def _delete_changed(self, checked: bool) -> None:
        self.settings.delete_source = checked

    def _refresh_targets(self) -> None:
        base = self.output_edit.text().strip()
        for entry in self._entries:
            target = str(Path(base) / entry.path.name) if base else "（待选择输出目录）"
            entry.target.setText(target)

    # ---------- 任务列表 ----------

    def add_paths(self, paths: list[Path]) -> None:
        """添加目录任务，重复路径只保留一次。"""
        existing = {entry.path.resolve() for entry in self._entries}
        for path in paths:
            if not path.is_dir():
                continue
            resolved = path.resolve()
            if resolved in existing:
                continue
            existing.add(resolved)
            self._append_row(Path(path))
        self._refresh_summary()
        self._refresh_targets()

    def _append_row(self, path: Path) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        name = QTableWidgetItem(path.name)
        name.setToolTip(str(path))
        self.table.setItem(row, 0, name)
        status = QTableWidgetItem("等待")
        self.table.setItem(row, 1, status)
        progress = QProgressBar()
        progress.setRange(0, 1)
        progress.setValue(0)
        progress.setTextVisible(False)
        self.table.setCellWidget(row, 2, progress)
        target = QTableWidgetItem("")
        target.setToolTip(str(path))
        self.table.setItem(row, 3, target)
        self._entries.append(TaskEntry(path, status, progress, target))

    def _choose_sources(self) -> None:
        selected = QFileDialog.getExistingDirectory(self, "选择 1 级目录")
        if selected:
            self.add_paths([Path(selected)])

    def _remove_selected(self) -> None:
        rows = sorted({index.row() for index in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.table.removeRow(row)
            if 0 <= row < len(self._entries):
                self._entries.pop(row)
        self._refresh_summary()

    def _clear(self) -> None:
        if self._worker is not None:
            return
        self.table.setRowCount(0)
        self._entries.clear()
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
        if not self._entries:
            QMessageBox.information(self, "还没有任务", "先把 1 级目录拖进来。")
            return
        output_text = self.output_edit.text().strip()
        if not output_text:
            QMessageBox.information(self, "缺少输出目录", "请先选择解压输出目录。")
            return
        output = Path(output_text)
        plans = plan_sources([entry.path for entry in self._entries], output)
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
        for entry, plan in zip(self._entries, plans, strict=False):
            entry.progress.setRange(0, max(len(plan.jobs), 1))
            entry.progress.setValue(0)
            entry.status.setText(f"等待（{len(plan.jobs)} 个包）" if plan.jobs else "没有压缩包")
        self._set_running(True)
        worker = ExtractWorker(
            plans, output, dict(self._tools), self.delete_check.isChecked(), self,
        )
        worker.log.connect(self.log_dialog.append)
        worker.row_progress.connect(self._row_progress)
        worker.row_finished.connect(self._row_finished)
        worker.finished_all.connect(self._finished)
        worker.failed.connect(self._worker_failed)
        worker.finished.connect(self._worker_released)
        self._worker = worker
        worker.start()

    def _cancel(self) -> None:
        if self._worker is not None:
            self._cancel_requested = True
            self.stop_action.setEnabled(False)
            self.summary.setText("正在停止…")
            self._worker.cancel()

    def _row_progress(self, index: int, done: int, total: int) -> None:
        if 0 <= index < len(self._entries):
            entry = self._entries[index]
            entry.progress.setRange(0, max(total, 1))
            entry.progress.setValue(done)
            entry.status.setText(f"解压中 {done}/{max(total, 1)}")

    def _row_finished(self, index: int, outcome: Outcome) -> None:
        if not 0 <= index < len(self._entries):
            return
        entry = self._entries[index]
        if outcome.skipped:
            entry.status.setText("没有压缩包")
            entry.progress.setRange(0, 1)
            entry.progress.setValue(0)
            return
        text = f"完成 {outcome.archives} 个包 / {outcome.entries} 个条目"
        if outcome.removed:
            text += f"，已删源 {outcome.removed}"
        if outcome.failures:
            text += f"，失败 {len(outcome.failures)}"
        entry.status.setText(text)
        entry.progress.setRange(0, 1)
        entry.progress.setValue(1)

    def _worker_failed(self, message: str) -> None:
        self._error = message

    def _finished(self, total: Outcome) -> None:
        self._set_running(False)
        if self._cancel_requested:
            for entry in self._entries:
                if entry.status.text().startswith("解压中"):
                    entry.status.setText("已停止")
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
        for action in (
            self.add_action, self.remove_action, self.clear_action, self.start_action,
        ):
            action.setEnabled(not running)
        self.stop_action.setEnabled(running)
        self.output_edit.setEnabled(not running)
        self.delete_check.setEnabled(not running)

    def _open_row_output(self, item: QTableWidgetItem) -> None:
        base = self.output_edit.text().strip()
        row = item.row()
        if base and 0 <= row < len(self._entries):
            path = Path(base) / self._entries[row].path.name
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

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
