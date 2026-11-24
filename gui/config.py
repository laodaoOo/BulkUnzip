"""界面设置持久化：输出目录、删除源文件与工具路径。"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from core.tools import application_directory

SETTINGS_PATH = application_directory() / "bulk_unzip.json"


@dataclass
class Settings:
    """上次使用的设置；工具路径为空表示自动查找。"""

    output_directory: str = ""
    delete_source: bool = False
    sevenzip_path: str = ""
    rar_path: str = ""


def load_settings(path: Path = SETTINGS_PATH) -> Settings:
    """读取设置文件；不存在或损坏时返回默认值。"""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Settings()
    if not isinstance(raw, dict):
        return Settings()
    known = {item.name for item in fields(Settings)}
    return Settings(**{key: value for key, value in raw.items() if key in known})


def save_settings(settings: Settings, path: Path = SETTINGS_PATH) -> None:
    """原子写入设置文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8",
    )
    os.replace(temporary, path)


__all__ = ["SETTINGS_PATH", "Settings", "load_settings", "save_settings"]
