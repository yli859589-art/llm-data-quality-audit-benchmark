from __future__ import annotations

import hashlib
from pathlib import Path


def _canonical_file_bytes(path: str | Path) -> bytes:
    data = Path(path).read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    return normalized.encode("utf-8")


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(_canonical_file_bytes(path)).hexdigest()
