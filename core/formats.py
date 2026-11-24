"""压缩格式识别：按文件头判断 zip / 7z / rar，不依赖扩展名。"""

from __future__ import annotations

from pathlib import Path

# 各格式的起始签名；RAR 有 v4 与 v5 两种。
SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"PK\x03\x04", "zip"),
    (b"PK\x05\x06", "zip"),
    (b"PK\x07\x08", "zip"),
    (b"7z\xbc\xaf\x27\x1c", "7z"),
    (b"Rar!\x1a\x07\x00", "rar"),
    (b"Rar!\x1a\x07\x01\x00", "rar"),
)

# 读取文件头的长度，足以覆盖上面所有签名。
HEADER_SIZE = max(len(signature) for signature, _ in SIGNATURES)


def detect_format(path: Path) -> str | None:
    """按文件头识别受支持的格式；无法识别返回 None。"""
    try:
        with path.open("rb") as stream:
            header = stream.read(HEADER_SIZE)
    except OSError:
        return None
    for signature, archive_format in SIGNATURES:
        if header.startswith(signature):
            return archive_format
    return None


__all__ = ["detect_format"]
