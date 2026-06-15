from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "artifacts" / "reports"
LEVEL3_TABLES = ROOT / "artifacts" / "level3_tables"
LEVEL3_REPORTS = ROOT / "artifacts" / "level3_reports"

PROTECTED_RESULT_FILES = {
    "artifacts/tables/main_results.csv": "EAB3478D19E04CAF97E07FC31FCD3CC36089C19320A64E96F7BAC9EB12D89921",
    "artifacts/stats/main_results.csv": "E40944BB6476D84E8C3FC65670B2DC5E7DB62CF47CA7FC6D0051768458CD0E32",
    "artifacts/cross_dataset/cross_dataset_results.csv": "8DA3E015146193FCD5D1F5F47A9E0A5ED84F55A4182B4BB5932DC657B8DAAD4C",
    "artifacts/runs/run_registry.jsonl": "A05A06FCA305CEDF2C46DBEAD17AC222A5F09E73AB105538479A049DF90A26CE",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = ROOT / path if not Path(path).is_absolute() else Path(path)
    return json.loads(config_path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    import hashlib

    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        canonical = data
    else:
        canonical = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest().upper()


def protected_hashes() -> dict[str, str]:
    return {name: sha256_file(ROOT / name) for name in PROTECTED_RESULT_FILES if (ROOT / name).exists()}


def protected_hashes_unchanged() -> bool:
    return all(protected_hashes().get(name) == expected for name, expected in PROTECTED_RESULT_FILES.items())


def _import_status(module_name: str) -> dict[str, Any]:
    try:
        module = __import__(module_name)
    except Exception as exc:
        return {"available": False, "version": None, "error": str(exc)}
    return {"available": True, "version": str(getattr(module, "__version__", "unknown")), "error": ""}


def _ram_gb() -> float | None:
    try:
        import psutil  # type: ignore

        return round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        return None


def _internet_available() -> bool:
    try:
        socket.create_connection(("huggingface.co", 443), timeout=5).close()
        with urllib.request.urlopen("https://huggingface.co", timeout=5) as response:
            return response.status < 500
    except Exception:
        return False


def collect_environment() -> dict[str, Any]:
    disk = shutil.disk_usage(ROOT)
    torch_status = _import_status("torch")
    datasets_status = _import_status("datasets")
    tokenizers_status = _import_status("tokenizers")
    transformers_status = _import_status("transformers")
    cuda_available = False
    gpu_name = None
    gpu_memory_gb = 0.0
    if torch_status["available"]:
        try:
            import torch

            cuda_available = bool(torch.cuda.is_available())
            if cuda_available:
                gpu_name = torch.cuda.get_device_name(0)
                props = torch.cuda.get_device_properties(0)
                gpu_memory_gb = round(float(props.total_memory) / (1024**3), 2)
        except Exception as exc:
            torch_status["cuda_error"] = str(exc)
    disk_free_gb = round(disk.free / (1024**3), 2)
    ram_gb = _ram_gb()
    storage_estimate_gb = 1500
    minimum_gpu_memory_gb = 16
    blocking = []
    if not torch_status["available"]:
        blocking.append("PyTorch is unavailable.")
    if not cuda_available:
        blocking.append("CUDA GPU is unavailable; medium/large-lite training cannot be executed honestly.")
    if gpu_memory_gb and gpu_memory_gb < minimum_gpu_memory_gb:
        blocking.append(f"GPU memory {gpu_memory_gb}GB is below the minimum {minimum_gpu_memory_gb}GB policy.")
    if disk_free_gb < storage_estimate_gb:
        blocking.append(f"Disk free space {disk_free_gb}GB is below the conservative {storage_estimate_gb}GB Level 3 estimate.")
    if not datasets_status["available"]:
        blocking.append("HuggingFace datasets package is unavailable.")
    if not tokenizers_status["available"] and not transformers_status["available"]:
        blocking.append("No tokenizer library is available for GPT-2/BPE mainline token counting.")
    internet = _internet_available()
    if not internet:
        blocking.append("Internet/HuggingFace access check failed.")
    cache_source = "HF_DATASETS_CACHE" if os.environ.get("HF_DATASETS_CACHE") else "HF_HOME" if os.environ.get("HF_HOME") else "default_huggingface_cache"
    feasible = not blocking
    return {
        "step": "step10B_level3_heavy_execution",
        "stage": "environment",
        "status": "passed" if feasible else "completed_with_failures",
        "checked_at": utc_now(),
        "python_version": sys.version,
        "python_executable_name": Path(sys.executable).name,
        "platform": sys.platform,
        "torch": torch_status,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
        "gpu_memory_gb": gpu_memory_gb,
        "cpu_cores": os.cpu_count(),
        "ram_gb": ram_gb,
        "disk_free_gb": disk_free_gb,
        "dataset_cache_directory": cache_source,
        "datasets": datasets_status,
        "tokenizers": tokenizers_status,
        "transformers": transformers_status,
        "internet_dataset_access_available": internet,
        "expected_storage_estimate_gb": storage_estimate_gb,
        "expected_runtime_estimate": "multi-day GPU execution for full 500M-token data and medium/large-lite training",
        "heavy_execution_feasible": feasible,
        "fallback_recommendation": "continue_step10B_only_after_gpu_storage_and_dataset_access_are_confirmed"
        if not feasible
        else "run_rehearsal_before_heavy_execution",
        "blocking_failures": blocking,
        "completed": False,
        "level3_completed_artifact": False,
        "heavy_execution_completed": False,
        "main_results_modified": False,
        "protected_hashes": protected_hashes(),
    }


def write_report(payload: dict[str, Any], name: str, title: str) -> tuple[Path, Path]:
    REPORTS.mkdir(parents=True, exist_ok=True)
    json_path = REPORTS / f"{name}.json"
    md_path = REPORTS / f"{name}.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        f"# {title}",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Step: `{payload.get('step')}`",
        f"- Stage: `{payload.get('stage')}`",
        f"- Completed: `{payload.get('completed')}`",
        f"- Heavy execution completed: `{payload.get('heavy_execution_completed')}`",
        f"- Level 3 completed artifact: `{payload.get('level3_completed_artifact')}`",
        "",
        "## Blocking Failures",
        "",
    ]
    blocking = payload.get("blocking_failures") or []
    lines.extend([f"- {item}" for item in blocking] if blocking else ["- none"])
    if payload.get("fallbacks_used"):
        lines.extend(["", "## Fallbacks Used", ""])
        lines.extend(f"- {item}" for item in payload["fallbacks_used"])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def environment_report() -> dict[str, Any]:
    path = REPORTS / "step10B_environment_report.json"
    return load_json(path)


def rehearsal_report() -> dict[str, Any]:
    return load_json(REPORTS / "step10B_rehearsal_report.json")


def blocked_stage_report(stage: str, blocking: list[str], extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "step": "step10B_level3_heavy_execution",
        "stage": stage,
        "status": "blocked",
        "completed": False,
        "evidence_level": f"level3_{stage}_blocked",
        "heavy_execution_completed": False,
        "level3_completed_artifact": False,
        "main_results_modified": False,
        "historical_results_modified": False,
        "blocking_failures": blocking,
        "fallbacks_used": [],
        "created_at": utc_now(),
        "protected_hashes": protected_hashes(),
    }
    if extra:
        payload.update(extra)
    return payload


def stage_blocking_from_environment() -> list[str]:
    env = environment_report()
    if not env:
        return ["Step 10B environment report is missing."]
    if env.get("heavy_execution_feasible") is not True:
        return list(env.get("blocking_failures") or ["Heavy execution environment is not feasible."])
    return []


def stage_blocking_from_rehearsal() -> list[str]:
    rehearsal = rehearsal_report()
    if not rehearsal:
        return ["Step 10B rehearsal report is missing."]
    if rehearsal.get("rehearsal_completed") is not True:
        return list(rehearsal.get("blocking_failures") or ["Rehearsal did not complete."])
    return []


def run_blocked_execution_stage(stage: str, report_name: str, title: str, readiness_key: str) -> dict[str, Any]:
    blocking = stage_blocking_from_environment() or stage_blocking_from_rehearsal()
    payload = blocked_stage_report(
        stage,
        blocking,
        {
            readiness_key: False,
            "scope": "blocked_before_heavy_execution",
            "smoke_only": False,
            "protocol_only": False,
            "new_level3_main_results_added": False,
        },
    )
    write_report(payload, report_name, title)
    print(f"{title}: {payload['status']}")
    return payload


def write_level3_status_artifacts(readiness: dict[str, Any]) -> None:
    LEVEL3_TABLES.mkdir(parents=True, exist_ok=True)
    LEVEL3_REPORTS.mkdir(parents=True, exist_ok=True)
    table_status = {
        "step": "step10B_level3_heavy_execution",
        "stage": "level3_tables",
        "status": "not_generated",
        "reason": "No completed Level 3 heavy evidence is available; result CSVs were not generated.",
        "registry_backed": True,
        "new_level3_main_results_added": False,
        "completed": False,
        "created_at": utc_now(),
    }
    (LEVEL3_TABLES / "step10B_table_generation_status.json").write_text(
        json.dumps(table_status, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (LEVEL3_TABLES / "README.md").write_text(
        "# Level 3 Tables\n\nNo Level 3 result tables were generated because Step 10B heavy execution did not complete the required data/training/evaluation gates.\n",
        encoding="utf-8",
    )
    (LEVEL3_REPORTS / "level3_limitations.md").write_text(
        "# Level 3 Limitations\n\nStep 10B is blocked before completed heavy execution. No 500M-token data, medium training, large-lite training, or official downstream evidence is claimed.\n",
        encoding="utf-8",
    )
    (LEVEL3_REPORTS / "level3_reproducibility.md").write_text(
        "# Level 3 Reproducibility\n\nThe repository preserves protocol, environment, rehearsal, and blocked-stage reports. Completed Level 3 result tables require future heavy execution and registry finalization.\n",
        encoding="utf-8",
    )
    (LEVEL3_REPORTS / "step10B_execution_summary.md").write_text(
        f"# Step 10B Execution Summary\n\nCurrent readiness: `{readiness.get('current_readiness')}`.\n\nHeavy execution completed: `{readiness.get('heavy_execution_completed')}`.\n",
        encoding="utf-8",
    )
