from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import shutil
import sys
import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in [SRC, SCRIPTS, SCRIPTS / "localmax"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from artifacts_v2.canonical_io import write_canonical_csv, write_canonical_json, write_canonical_text

REPORTS = ROOT / "artifacts" / "reports"
V2_DATA = ROOT / "artifacts" / "localmax_v2_data"
V2_FILTERS = ROOT / "artifacts" / "localmax_v2_filters"
V2_TRAINING = ROOT / "artifacts" / "localmax_v2_training"
V2_EVALUATION = ROOT / "artifacts" / "localmax_v2_evaluation"
V2_DOWNSTREAM = ROOT / "artifacts" / "localmax_v2_downstream"
V2_ANALYSIS = ROOT / "artifacts" / "localmax_v2_analysis"
V2_TABLES = ROOT / "artifacts" / "localmax_v2_tables"
V2_RELEASE = ROOT / "artifacts" / "localmax_v2_release"

PROTECTED_RESULT_FILES = {
    "artifacts/tables/main_results.csv": "EAB3478D19E04CAF97E07FC31FCD3CC36089C19320A64E96F7BAC9EB12D89921",
    "artifacts/stats/main_results.csv": "E40944BB6476D84E8C3FC65670B2DC5E7DB62CF47CA7FC6D0051768458CD0E32",
    "artifacts/cross_dataset/cross_dataset_results.csv": "8DA3E015146193FCD5D1F5F47A9E0A5ED84F55A4182B4BB5932DC657B8DAAD4C",
    "artifacts/runs/run_registry.jsonl": "A05A06FCA305CEDF2C46DBEAD17AC222A5F09E73AB105538479A049DF90A26CE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def load_config(path: str | Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_json(path: str | Path) -> dict[str, Any]:
    target = ROOT / path if not isinstance(path, Path) else path
    if not target.exists():
        return {}
    payload = json.loads(target.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    return write_canonical_json(path, payload)


def write_text(path: Path, text: str) -> Path:
    return write_canonical_text(path, text)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> Path:
    return write_canonical_csv(path, fieldnames, rows)


def write_jsonl_gz(path: Path, rows: Iterable[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as gz:
            with io.TextIOWrapper(gz, encoding="utf-8", newline="\n") as handle:
                for row in rows:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def open_jsonl_gz_writer(path: Path) -> io.TextIOWrapper:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = path.open("wb")
    gz = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
    return io.TextIOWrapper(gz, encoding="utf-8", newline="\n")


def iter_jsonl_any(path: Path) -> Iterator[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:  # type: ignore[arg-type]
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def protected_hashes() -> dict[str, str]:
    return {name: sha256_file(ROOT / name) for name in PROTECTED_RESULT_FILES if (ROOT / name).exists()}


def protected_hashes_unchanged() -> bool:
    actual = protected_hashes()
    return all(actual.get(name) == expected for name, expected in PROTECTED_RESULT_FILES.items())


def gpt2_tokenizer() -> Any:
    from transformers import AutoTokenizer  # type: ignore

    tokenizer = AutoTokenizer.from_pretrained("gpt2")
    tokenizer.model_max_length = 10**12
    return tokenizer


def disk_free_gb() -> float:
    return round(shutil.disk_usage(ROOT).free / (1024**3), 2)


def directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def status_payload(stage: str, ready: bool, blocking: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "step": "step10B_localmax_v2",
        "stage": stage,
        "status": "completed" if ready else "blocked",
        "created_at": utc_now(),
        "completed": ready,
        "current_readiness": "LOCAL_MAX_V2_STRONG_EVIDENCE_COMPLETED" if ready else "LOCAL_MAX_V2_PARTIAL_WITH_REAL_EVIDENCE",
        "level3_completed_artifact": False,
        "ccf_b_ready_claimed": False,
        "weak_ccf_a_claimed": False,
        "sota_claimed": False,
        "historical_results_modified": not protected_hashes_unchanged(),
        "main_results_modified": False,
        "blocking_failures": sorted(set(blocking)),
        "protected_hashes": protected_hashes(),
    }
    if extra:
        payload.update(extra)
    return payload


def write_report(payload: dict[str, Any], name: str, title: str) -> tuple[Path, Path]:
    json_path = write_json(REPORTS / f"{name}.json", payload)
    lines = [
        f"# {title}",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Current readiness: `{payload.get('current_readiness')}`",
        f"- Completed: `{payload.get('completed')}`",
        f"- Historical results modified: `{payload.get('historical_results_modified')}`",
        "",
        "## Blocking Failures",
        "",
    ]
    blocking = payload.get("blocking_failures") or []
    lines.extend([f"- {item}" for item in blocking] if blocking else ["- none"])
    notes = payload.get("notes")
    if notes:
        lines.extend(["", "## Notes", ""])
        if isinstance(notes, list):
            lines.extend(f"- {item}" for item in notes)
        else:
            lines.append(f"- {notes}")
    md_path = write_text(REPORTS / f"{name}.md", "\n".join(lines))
    return json_path, md_path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", newline="") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def simple_markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def ensure_disk_reserve(reserve_gb: float = 25.0) -> None:
    free = disk_free_gb()
    if free < reserve_gb:
        raise RuntimeError(f"Disk free space {free}GB is below required reserve {reserve_gb}GB")


def cpu_count() -> int:
    return os.cpu_count() or 1
