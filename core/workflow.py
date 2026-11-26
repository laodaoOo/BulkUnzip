"""批量解压：把 1 级目录下各 2 级目录里的压缩包解到输出目录的同名两层目录。

规则与 NestPack 的解压页一致：1 级、2 级目录名保持不变；压缩包内只有一层
外壳文件夹时剥掉这一层；与已有内容重名时按系统习惯追加序号；可选在解开后
删除源压缩包，目录清空后一并移除。
"""

from __future__ import annotations

import os
import queue
import re
import shutil
import subprocess
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .formats import detect_format
from .tools import extract_command

# 解压工作目录，位于输出目录下，成功后清理。
WORK_DIRECTORY_NAME = ".bulk_unzip_tmp"

# 视为成功的退出码：0 正常，1 表示部分文件被跳过（工具自身仍算完成）。
SUCCESS_CODES = {0, 1}

# 工具输出里的百分比（7z 的 -bsp1 与 RAR 的默认进度）。
_PROGRESS_PATTERN = re.compile(r"(\d{1,3})%")

# 保留的输出尾巴长度，用于失败时取错误行。
_TAIL_LIMIT = 4000


class CancelledError(RuntimeError):
    """用户中途取消。"""


@dataclass(frozen=True)
class ExtractJob:
    """一个待解压的压缩包、它所在的 2 级目录与落盘目录。"""

    archive: Path
    target: Path
    folder: Path
    archive_format: str


@dataclass
class SourcePlan:
    """一个 1 级目录的待办任务。"""

    source: Path
    jobs: list[ExtractJob] = field(default_factory=list)


@dataclass
class Outcome:
    """一次执行的结果统计。"""

    archives: int = 0
    entries: int = 0
    removed: int = 0
    skipped: int = 0
    renames: list[tuple[str, str]] = field(default_factory=list)
    failures: list[tuple[str, str]] = field(default_factory=list)

    def merge(self, other: Outcome) -> None:
        """把另一个 1 级目录的结果并入总计。"""
        self.archives += other.archives
        self.entries += other.entries
        self.removed += other.removed
        self.skipped += other.skipped
        self.renames.extend(other.renames)
        self.failures.extend(other.failures)


def plan_sources(sources: Sequence[Path], output: Path) -> list[SourcePlan]:
    """扫描每个 1 级目录的 2 级目录，收集其中的压缩包。"""
    plans: list[SourcePlan] = []
    for source in sources:
        if not source.is_dir():
            raise ValueError(f"来源必须是文件夹：{source}")
        plan = SourcePlan(source)
        for directory in _sorted_children(source):
            if not directory.is_dir():
                continue
            for item in _sorted_children(directory):
                if not item.is_file():
                    continue
                archive_format = detect_format(item)
                if archive_format is None:
                    continue
                if _is_later_volume(item.name):
                    continue
                plan.jobs.append(ExtractJob(
                    archive=item,
                    target=output / source.name / directory.name,
                    folder=directory,
                    archive_format=archive_format,
                ))
        plans.append(plan)
    return plans


def extract_source(
    plan: SourcePlan,
    output: Path,
    tools: dict[str, Path | None],
    *,
    delete_source: bool = False,
    cancel_event: threading.Event | None = None,
    log: Callable[[str], None] | None = None,
    progress: Callable[[int, int], None] | None = None,
    percent: Callable[[int], None] | None = None,
) -> Outcome:
    """解开一个 1 级目录里的全部压缩包，按 2 级目录增量清理。"""
    outcome = Outcome()
    total = len(plan.jobs)
    if total == 0:
        outcome.skipped = 1
        return outcome
    work_root = output / WORK_DIRECTORY_NAME / _safe_name(plan.source.name)
    try:
        done = 0
        for folder, jobs in _group_by_folder(plan.jobs):
            failed = False
            for job in jobs:
                _check_cancel(cancel_event)
                if progress is not None:
                    progress(done, total)
                if percent is not None:
                    percent(0)
                _log(log, f"解压：{job.archive.name}")
                success = _run_job(
                    job, work_root, tools, cancel_event, log, outcome, percent,
                )
                done += 1
                if progress is not None:
                    progress(done, total)
                if success:
                    outcome.archives += 1
                    if percent is not None:
                        percent(100)
                else:
                    failed = True
            if delete_source and not failed:
                _remove_folder_sources(folder, jobs, outcome, log)
        if delete_source:
            _remove_empty_directory(plan.source, log)
    finally:
        shutil.rmtree(output / WORK_DIRECTORY_NAME, ignore_errors=True)
    return outcome


def _run_job(
    job: ExtractJob,
    work_root: Path,
    tools: dict[str, Path | None],
    cancel_event: threading.Event | None,
    log: Callable[[str], None] | None,
    outcome: Outcome,
    percent: Callable[[int], None] | None = None,
) -> bool:
    """解压单个压缩包并并入目标目录；失败只记录。"""
    tool = tools.get("7z" if job.archive_format in ("zip", "7z") else "rar")
    if tool is None:
        outcome.failures.append((job.archive.name, _missing_tool_message(job.archive_format)))
        return False
    work = work_root / _safe_name(job.archive.name)
    work.mkdir(parents=True, exist_ok=True)
    try:
        code, detail = _run_command(
            extract_command(tool, job.archive_format, job.archive, work),
            cancel_event, percent,
        )
    except CancelledError:
        raise
    if code not in SUCCESS_CODES:
        outcome.failures.append((job.archive.name, detail or f"工具返回错误代码 {code}"))
        return False
    payload = _single_directory(work) or work
    job.target.mkdir(parents=True, exist_ok=True)
    for entry in _sorted_children(payload):
        target = _free_path(job.target, entry.name)
        if target.name != entry.name:
            outcome.renames.append((
                f"{job.folder.name}/{entry.name}",
                f"{job.target.name}/{target.name}",
            ))
        shutil.move(str(entry), str(target))
        outcome.entries += 1
    return True


def _remove_folder_sources(
    folder: Path,
    jobs: Sequence[ExtractJob],
    outcome: Outcome,
    log: Callable[[str], None] | None,
) -> None:
    """删除这个 2 级目录里已解开的源压缩包，目录清空后一并移除。"""
    for job in jobs:
        try:
            job.archive.unlink()
        except OSError as error:
            _log(log, f"无法删除 {job.archive.name}：{error}")
            continue
        outcome.removed += 1
    _remove_empty_directory(folder, log)


def _run_command(
    command: list[str],
    cancel_event: threading.Event | None,
    percent: Callable[[int], None] | None = None,
) -> tuple[int, str]:
    """运行归档工具，边读输出边回报百分比；返回退出码与错误摘要。"""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        bufsize=0, creationflags=flags,
    )
    stream = process.stdout
    chunks: queue.Queue[bytes | None] = queue.Queue()

    def pump() -> None:
        try:
            while True:
                piece = stream.read(512) if stream is not None else b""
                if not piece:
                    break
                chunks.put(piece)
        finally:
            chunks.put(None)

    threading.Thread(target=pump, daemon=True).start()
    tail = bytearray()
    pending = ""
    last = -1
    while True:
        if cancel_event is not None and cancel_event.is_set():
            process.kill()
            process.wait()
            raise CancelledError("已取消")
        try:
            piece = chunks.get(timeout=0.2)
        except queue.Empty:
            if process.poll() is not None:
                break
            continue
        if piece is None:
            break
        tail.extend(piece)
        if len(tail) > _TAIL_LIMIT:
            del tail[: len(tail) - _TAIL_LIMIT]
        if percent is not None:
            pending += piece.decode("utf-8", "replace")
            for match in _PROGRESS_PATTERN.finditer(pending):
                value = int(match.group(1))
                if 0 <= value <= 100 and value != last:
                    last = value
                    percent(value)
            pending = pending[-8:]
    process.wait()
    if stream is not None:
        stream.close()
    text = tail.decode("utf-8", "replace")
    lines = [line.strip() for line in re.split(r"[\r\n]+", text) if line.strip()]
    return process.returncode, lines[-1] if lines else ""


def _missing_tool_message(archive_format: str) -> str:
    """工具缺失时的说明。"""
    tool = "WinRAR（Rar.exe）" if archive_format == "rar" else "7-Zip（7z.exe）"
    return f"缺少 {tool}，无法解开该压缩包"


def _check_cancel(cancel_event: threading.Event | None) -> None:
    """在步骤之间检查取消。"""
    if cancel_event is not None and cancel_event.is_set():
        raise CancelledError("已取消")


def _single_directory(root: Path) -> Path | None:
    """压缩包内只有一层目录时返回该目录，用于剥掉外壳文件夹。"""
    entries = list(root.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return None


def _free_path(directory: Path, name: str) -> Path:
    """返回不冲突的目标路径；重名时按系统习惯追加序号。"""
    candidate = directory / name
    if not candidate.exists():
        return candidate
    stem = Path(name).stem
    suffix = Path(name).suffix
    index = 2
    while True:
        candidate = directory / f"{stem} ({index}){suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def _remove_empty_directory(path: Path, log: Callable[[str], None] | None) -> None:
    """目录清空后删除，否则保留。"""
    try:
        path.rmdir()
    except OSError:
        return
    _log(log, f"已删除空目录：{path}")


def _sorted_children(directory: Path) -> list[Path]:
    """按名称不区分大小写排序，保证处理顺序稳定。"""
    return sorted(directory.iterdir(), key=lambda item: item.name.casefold())


def _group_by_folder(jobs: Sequence[ExtractJob]) -> list[tuple[Path, list[ExtractJob]]]:
    """按 2 级目录分组，保持扫描顺序。"""
    groups: list[tuple[Path, list[ExtractJob]]] = []
    for job in jobs:
        if groups and groups[-1][0] == job.folder:
            groups[-1][1].append(job)
        else:
            groups.append((job.folder, [job]))
    return groups


def _safe_name(name: str) -> str:
    """把来源名转成可用的临时目录名。"""
    return "".join("_" if char in '\\/:*?"<>|' else char for char in name) or "_"


def _is_later_volume(name: str) -> bool:
    """分卷套只处理第一卷：.001 / .part2.rar 这类后续卷跳过。"""
    lowered = name.lower()
    if lowered.endswith(".001"):
        return False
    for suffix in (".002", ".003", ".004", ".005", ".006", ".007", ".008", ".009"):
        if lowered.endswith(suffix):
            return True
    return ".part" in lowered and not lowered.endswith(".part1.rar")


def _log(callback: Callable[[str], None] | None, message: str) -> None:
    """写一条日志。"""
    if callback is not None:
        callback(message)


__all__ = [
    "CancelledError",
    "ExtractJob",
    "Outcome",
    "SourcePlan",
    "extract_source",
    "plan_sources",
]
