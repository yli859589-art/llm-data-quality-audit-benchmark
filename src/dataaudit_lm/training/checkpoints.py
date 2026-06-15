from __future__ import annotations

from pathlib import Path
from typing import Any

import torch

from dataaudit_lm.integrity.hashing import sha256_file


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def save_checkpoint(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, path)
    return {"checkpoint_path": _display_path(path), "checkpoint_sha256": sha256_file(path)}


def load_checkpoint(path: Path) -> dict[str, Any]:
    payload = torch.load(path, map_location="cpu")
    if not isinstance(payload, dict):
        raise ValueError("checkpoint payload must be a dictionary")
    return payload
