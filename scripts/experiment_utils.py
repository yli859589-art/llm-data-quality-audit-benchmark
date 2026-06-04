from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))


def load_json_yaml(path: str | Path) -> dict[str, Any]:
    from course_project_suite.llm_benchmark.config import load_yaml_config

    return load_yaml_config(root / path if not Path(path).is_absolute() else path)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
