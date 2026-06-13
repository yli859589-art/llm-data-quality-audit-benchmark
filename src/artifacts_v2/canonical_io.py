from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _final_newline(text: str) -> str:
    text = _normalize_newlines(text)
    return text.rstrip("\n") + "\n"


def write_canonical_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_final_newline(text), encoding="utf-8", newline="\n")
    return path


def write_canonical_json(path: Path, payload: Any) -> Path:
    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
    return write_canonical_text(path, content)


def write_canonical_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
    return write_canonical_text(path, "\n".join(lines))


def write_canonical_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})
    return path


def canonicalize_text_bytes(path: Path) -> Path:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    return write_canonical_text(path, text)
