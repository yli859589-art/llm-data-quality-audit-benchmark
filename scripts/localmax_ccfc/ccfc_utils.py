from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
SCRIPTS = ROOT / "scripts"
for path in [SRC, SCRIPTS, SCRIPTS / "localmax", SCRIPTS / "localmax_v2"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from artifacts_v2.canonical_io import (
    write_canonical_csv,
    write_canonical_json,
    write_canonical_text,
)

REPORTS = ROOT / "artifacts" / "reports"
V2_DATA = ROOT / "artifacts" / "localmax_v2_data"
V2_TRAINING = ROOT / "artifacts" / "localmax_v2_training"
CCFC_FILTERS = ROOT / "artifacts" / "localmax_ccfc_filters"
CCFC_TRAINING = ROOT / "artifacts" / "localmax_ccfc_training"
CCFC_EVALUATION = ROOT / "artifacts" / "localmax_ccfc_evaluation"
CCFC_DOWNSTREAM = ROOT / "artifacts" / "localmax_ccfc_downstream"
CCFC_ANALYSIS = ROOT / "artifacts" / "localmax_ccfc_analysis"
CCFC_TABLES = ROOT / "artifacts" / "localmax_ccfc_tables"
CCFC_RELEASE = ROOT / "artifacts" / "localmax_ccfc_release"

PROTECTED_RESULT_FILES = {
    "artifacts/tables/main_results.csv": "D8E593744EEB95CECB422C600CEC89C70279B28E09FCD3DE96AA8D1C9F2A7C3F",
    "artifacts/stats/main_results.csv": "38AA59CE82B2511FBF711D4B696E7B47C7C89F94D2ABCA0835D75AC0F14057B4",
    "artifacts/cross_dataset/cross_dataset_results.csv": "5003F1534231EEDAEE6B501D6F9769C45CEF749CFE37921E8AB10CCE12C73A86",
    "artifacts/runs/run_registry.jsonl": "D9EF6C857EC44CEF1659F1444752C6B4FC2C86C443F27665621CEA39B45086D8",
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


def canonical_sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest().upper()


def protected_hashes() -> dict[str, str]:
    return {
        name: canonical_sha256_file(ROOT / name)
        for name in PROTECTED_RESULT_FILES
        if (ROOT / name).exists()
    }


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


def ensure_disk_reserve(reserve_gb: float = 20.0) -> None:
    free = disk_free_gb()
    if free < reserve_gb:
        raise RuntimeError(f"Disk free space {free}GB is below required reserve {reserve_gb}GB")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def status_payload(
    stage: str, ready: bool, blocking: list[str], extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "step": "localmax_ccfc_strengthening",
        "stage": stage,
        "status": "completed" if ready else "blocked",
        "created_at": utc_now(),
        "completed": ready,
        "current_readiness": "CCFC_CANDIDATE_EVIDENCE" if ready else "CCFC_PARTIAL_EVIDENCE",
        "ccf_c_paper_claimed": False,
        "ccf_b_ready_claimed": False,
        "level3_completed_artifact": False,
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
        f"- CCF-C paper claimed: `{payload.get('ccf_c_paper_claimed')}`",
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
