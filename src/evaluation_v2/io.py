from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def project_relative(path: str | Path, root: Path) -> str:
    if not path:
        return ""
    value = Path(path)
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return value.as_posix()


def resolve_path(path: str | Path, root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root / value


def read_json(path: str | Path, root: Path | None = None) -> dict[str, Any]:
    value = resolve_path(path, root) if root is not None else Path(path)
    return json.loads(value.read_text(encoding="utf-8"))


def read_jsonl(path: str | Path, root: Path | None = None) -> list[dict[str, Any]]:
    value = resolve_path(path, root) if root is not None else Path(path)
    rows = []
    for line in value.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
