from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def resolve_path(path: str | Path, root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root / value


def project_relative(path: str | Path, root: Path) -> str:
    if not path:
        return ""
    value = Path(path)
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return value.as_posix()


def read_json(path: str | Path, root: Path | None = None) -> dict[str, Any]:
    value = resolve_path(path, root) if root is not None else Path(path)
    return json.loads(value.read_text(encoding="utf-8"))


def read_jsonl(path: str | Path, root: Path | None = None) -> list[dict[str, Any]]:
    value = resolve_path(path, root) if root is not None else Path(path)
    rows: list[dict[str, Any]] = []
    for line in value.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_csv(path: str | Path, root: Path | None = None) -> list[dict[str, str]]:
    value = resolve_path(path, root) if root is not None else Path(path)
    with value.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        ordered: list[str] = []
        for row in rows:
            for key in row:
                if key not in ordered:
                    ordered.append(key)
        fieldnames = ordered
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def mean_or_none(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None

