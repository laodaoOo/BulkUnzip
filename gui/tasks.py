"""后台执行：按顺序解开各 1 级目录，并逐行回报进度。"""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core import CancelledError, Outcome, SourcePlan, extract_source


class ExtractWorker(QThread):
    """在后台线程里逐个 1 级目录执行；界面只负责展示。"""

    log = Signal(str)
    row_started = Signal(int)
    row_progress = Signal(int, int, int)
    row_finished = Signal(int, object)
    finished_all = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        plans: list[SourcePlan],
        output: Path,
        tools: dict[str, Path | None],
        delete_source: bool,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._plans = plans
        self._output = output
        self._tools = tools
        self._delete_source = delete_source
        self._cancel = threading.Event()
        self.was_cancelled = False

    def cancel(self) -> None:
        """请求停止：结束当前压缩包并跳过后续目录。"""
        self._cancel.set()

    def run(self) -> None:
        total = Outcome()
        try:
            for index, plan in enumerate(self._plans):
                if self._cancel.is_set():
                    raise CancelledError("已取消")
                self.row_started.emit(index)
                outcome = extract_source(
                    plan, self._output, self._tools,
                    delete_source=self._delete_source,
                    cancel_event=self._cancel,
                    log=self.log.emit,
                    progress=lambda done, count, row=index: self.row_progress.emit(
                        row, done, count,
                    ),
                )
                total.merge(outcome)
                self.row_finished.emit(index, outcome)
        except CancelledError:
            self.was_cancelled = True
        except Exception as error:  # noqa: BLE001 - 后台线程兜底，交给界面提示
            self.failed.emit(str(error))
        finally:
            self.finished_all.emit(total)


__all__ = ["ExtractWorker"]
