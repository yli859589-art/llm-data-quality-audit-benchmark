from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - optional dependency probe
    psutil = None  # type: ignore

try:
    import torch  # type: ignore
except Exception:  # pragma: no cover - optional dependency probe
    torch = None  # type: ignore


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from artifacts_v2.canonical_io import write_canonical_csv, write_canonical_json, write_canonical_text

REPORTS = ROOT / "artifacts" / "reports"
LOCALMAX_DATA = ROOT / "artifacts" / "localmax_data"
LOCALMAX_TOKENIZERS = ROOT / "artifacts" / "localmax_tokenizers"
LOCALMAX_FILTERS = ROOT / "artifacts" / "localmax_filters"
LOCALMAX_TRAINING = ROOT / "artifacts" / "localmax_training"
LOCALMAX_EVALUATION = ROOT / "artifacts" / "localmax_evaluation"
LOCALMAX_MECHANISMS = ROOT / "artifacts" / "localmax_mechanisms"
LOCALMAX_TABLES = ROOT / "artifacts" / "localmax_tables"
LOCALMAX_REPORTS = ROOT / "artifacts" / "localmax_reports"
LOCALMAX_FIGURES = ROOT / "artifacts" / "localmax_figures"

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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def protected_hashes() -> dict[str, str]:
    return {name: sha256_file(ROOT / name) for name in PROTECTED_RESULT_FILES if (ROOT / name).exists()}


def protected_hashes_unchanged() -> bool:
    actual = protected_hashes()
    return all(actual.get(name) == expected for name, expected in PROTECTED_RESULT_FILES.items())


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> Path:
    return write_canonical_json(path, payload)


def write_markdown(path: Path, title: str, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocking = payload.get("blocking_failures") or []
    lines = [
        f"# {title}",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Current readiness: `{payload.get('current_readiness', payload.get('readiness', 'n/a'))}`",
        f"- Completed: `{payload.get('completed')}`",
        f"- LocalMax completed: `{payload.get('localmax_completed', False)}`",
        f"- Level 3 completed: `{payload.get('level3_completed', False)}`",
        f"- Main results modified: `{payload.get('main_results_modified', False)}`",
        "",
        "## Blocking Failures",
        "",
    ]
    lines.extend([f"- {item}" for item in blocking] if blocking else ["- none"])
    notes = payload.get("notes")
    if isinstance(notes, list) and notes:
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {item}" for item in notes)
    elif isinstance(notes, str) and notes:
        lines.extend(["", "## Notes", "", f"- {notes}"])
    return write_canonical_text(path, "\n".join(lines))


def write_report(payload: dict[str, Any], name: str, title: str) -> tuple[Path, Path]:
    json_path = write_json(REPORTS / f"{name}.json", payload)
    md_path = write_markdown(REPORTS / f"{name}.md", title, payload)
    return json_path, md_path


def import_status(module_name: str) -> dict[str, Any]:
    try:
        module = __import__(module_name)
    except Exception as exc:
        return {"available": False, "version": None, "error": str(exc)}
    return {"available": True, "version": str(getattr(module, "__version__", "unknown")), "error": ""}


def collect_localmax_environment() -> dict[str, Any]:
    disk = shutil.disk_usage(ROOT)
    disk_free_gb = round(disk.free / (1024**3), 2)
    ram_gb = round(psutil.virtual_memory().total / (1024**3), 2) if psutil else None
    cuda_available = False
    gpu_name = None
    gpu_memory_gb = 0.0
    if torch is not None:
        try:
            cuda_available = bool(torch.cuda.is_available())
            if cuda_available:
                gpu_name = torch.cuda.get_device_name(0)
                props = torch.cuda.get_device_properties(0)
                gpu_memory_gb = round(float(props.total_memory) / (1024**3), 2)
        except Exception:
            cuda_available = False
    required_modules = {
        name: import_status(name)
        for name in ["torch", "datasets", "transformers", "tokenizers", "psutil", "numpy", "pandas"]
    }
    missing = [name for name, status in required_modules.items() if not status["available"]]
    partial_feasible = disk_free_gb >= 20 and not missing and (ram_gb is None or ram_gb >= 8)
    blocking = []
    if missing:
        blocking.append("Missing required Python modules for LocalMax execution: " + ", ".join(missing))
    if disk_free_gb < 20:
        blocking.append(f"Disk free space {disk_free_gb}GB is below the 20GB LocalMax partial floor.")
    if ram_gb is not None and ram_gb < 8:
        blocking.append(f"System RAM {ram_gb}GB is below the 8GB LocalMax partial floor.")
    if gpu_memory_gb and gpu_memory_gb < 8:
        blocking.append(f"GPU memory {gpu_memory_gb}GB is below the 8GB local training floor.")
    return {
        "step": "step10B_localmax_execution",
        "stage": "environment",
        "status": "completed" if partial_feasible else "blocked",
        "created_at": utc_now(),
        "python_version": sys.version.split()[0],
        "python_executable_name": Path(sys.executable).name,
        "platform": sys.platform,
        "cpu_cores": os.cpu_count(),
        "ram_gb": ram_gb,
        "disk_free_gb": disk_free_gb,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name or "unavailable_or_not_reported",
        "gpu_memory_gb": gpu_memory_gb,
        "required_modules": required_modules,
        "localmax_feasible": partial_feasible,
        "recommended_token_budget_per_dataset": 50_000_000,
        "max_attempt_token_budget_per_dataset": 100_000_000,
        "minimum_localmax_dataset_tokens": 20_000_000,
        "recommended_main_model": "small_25m_40m",
        "selected_model": "medium_lite_60m_80m",
        "true_medium_completed": False,
        "large_lite_completed": False,
        "level3_completed_possible_on_this_machine": False,
        "level3_completed": False,
        "localmax_completed": False,
        "main_results_modified": False,
        "historical_results_modified": not protected_hashes_unchanged(),
        "blocking_failures": blocking,
        "notes": [
            "This environment can support bounded LocalMax bookkeeping and tokenizer/data audits.",
            "It is not treated as sufficient for completed Level 3 heavy execution.",
        ],
        "protected_hashes": protected_hashes(),
    }


def read_text_records(paths: list[Path]) -> list[str]:
    records: list[str] = []
    for path in paths:
        if not path.exists():
            continue
        if path.suffix == ".jsonl":
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    text = str(payload.get("text", ""))
                except json.JSONDecodeError:
                    text = line
                if text:
                    records.append(text)
        else:
            text = path.read_text(encoding="utf-8")
            if text:
                records.append(text)
    return records


def source_dataset_specs() -> list[dict[str, Any]]:
    return [
        {
            "dataset_id": "wikitext2_paper",
            "dataset_name": "WikiText-2 official split local mirror",
            "source_manifest_path": "artifacts/data/wikitext2_paper/data_manifest.json",
            "split_paths": {
                "train": "data/real/wikitext2_raw/train.txt",
                "validation": "data/real/wikitext2_raw/dev.txt",
                "test": "data/real/wikitext2_raw/test.txt",
            },
            "is_streaming_sample": False,
        },
        {
            "dataset_id": "openwebtext_streaming",
            "dataset_name": "OpenWebText streaming sample",
            "source_manifest_path": "artifacts/data/openwebtext_streaming/data_manifest.json",
            "split_paths": {
                "train": "artifacts/data/openwebtext_streaming/splits/train.jsonl",
                "validation": "artifacts/data/openwebtext_streaming/splits/dev.jsonl",
                "test": "artifacts/data/openwebtext_streaming/splits/test.jsonl",
            },
            "is_streaming_sample": True,
        },
        {
            "dataset_id": "c4_en_streaming",
            "dataset_name": "C4 English streaming sample",
            "source_manifest_path": "artifacts/data/c4_en_streaming/data_manifest.json",
            "split_paths": {
                "train": "artifacts/data/c4_en_streaming/splits/train.jsonl",
                "validation": "artifacts/data/c4_en_streaming/splits/dev.jsonl",
                "test": "artifacts/data/c4_en_streaming/splits/test.jsonl",
            },
            "is_streaming_sample": True,
        },
    ]


def gpt2_tokenizer() -> Any:
    from transformers import AutoTokenizer  # type: ignore

    return AutoTokenizer.from_pretrained("gpt2")


def count_tokens(tokenizer: Any, texts: list[str]) -> int:
    total = 0
    for text in texts:
        total += len(tokenizer.encode(text))
    return total


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> Path:
    return write_canonical_csv(path, fieldnames, rows)


def status_payload(stage: str, ready: bool, blocking: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "step": "step10B_localmax_execution",
        "stage": stage,
        "status": "completed" if ready else "blocked",
        "created_at": utc_now(),
        "completed": ready,
        "localmax_completed": False,
        "level3_completed": False,
        "level3_completed_artifact": False,
        "true_medium_completed": False,
        "large_lite_completed": False,
        "official_downstream_completed": False,
        "statistical_significance_claim_allowed": False,
        "main_results_modified": False,
        "historical_results_modified": not protected_hashes_unchanged(),
        "blocking_failures": blocking,
        "protected_hashes": protected_hashes(),
    }
    if extra:
        payload.update(extra)
    return payload
