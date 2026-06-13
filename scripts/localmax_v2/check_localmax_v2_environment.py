from __future__ import annotations

import importlib.util
import json
import platform
import sys
import time
from typing import Any

from localmax_v2_utils import ROOT, directory_size_bytes, disk_free_gb, status_payload, write_report


def _module_status(name: str) -> dict[str, Any]:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return {"available": False, "version": None}
    module = __import__(name)
    return {"available": True, "version": str(getattr(module, "__version__", "unknown"))}


def main() -> None:
    started = time.perf_counter()
    modules = {name: _module_status(name) for name in ["torch", "datasets", "transformers", "tokenizers", "numpy", "pandas", "matplotlib", "psutil"]}
    missing = [name for name, status in modules.items() if not status["available"]]
    cuda_available = False
    gpu_name = "unavailable"
    gpu_memory_gb = 0.0
    cuda_version = None
    ram_gb = None
    try:
        import psutil  # type: ignore

        ram_gb = round(psutil.virtual_memory().total / (1024**3), 2)
    except Exception:
        pass
    try:
        import torch  # type: ignore

        cuda_available = bool(torch.cuda.is_available())
        cuda_version = torch.version.cuda
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            props = torch.cuda.get_device_properties(0)
            gpu_memory_gb = round(float(props.total_memory) / (1024**3), 2)
    except Exception:
        pass
    free_gb = disk_free_gb()
    estimated_data_size_gb = 4.0
    estimated_training_artifacts_gb = 2.0
    max_safe_data_budget_gb = max(0.0, min(20.0, free_gb - 25.0 - estimated_training_artifacts_gb))
    blocking: list[str] = []
    if missing:
        blocking.append("Missing required modules: " + ", ".join(missing))
    if free_gb < 25.0:
        blocking.append(f"Disk free space {free_gb}GB is below 25GB reserve.")
    if max_safe_data_budget_gb < estimated_data_size_gb:
        blocking.append(
            f"Projected data budget {estimated_data_size_gb}GB exceeds safe budget {max_safe_data_budget_gb:.2f}GB."
        )
    if ram_gb is not None and ram_gb < 8:
        blocking.append(f"RAM {ram_gb}GB is below minimum local execution floor.")
    selected_tier = "Tier B"
    ready = not blocking
    report = status_payload(
        "environment",
        ready,
        blocking,
        {
            "status": "completed" if ready else "blocked",
            "current_readiness": "LOCAL_MAX_V2_PREFLIGHT_READY" if ready else "LOCAL_MAX_V2_BLOCKED",
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu": platform.processor() or "not_reported",
            "cpu_cores": ROOT.anchor and (__import__("os").cpu_count() or 1),
            "ram_gb": ram_gb,
            "disk_free_gb": free_gb,
            "disk_reserve_gb": 25,
            "existing_localmax_v2_artifacts_gb": round(
                sum(directory_size_bytes(ROOT / "artifacts" / name) for name in [
                    "localmax_v2_data",
                    "localmax_v2_filters",
                    "localmax_v2_training",
                    "localmax_v2_evaluation",
                    "localmax_v2_analysis",
                    "localmax_v2_tables",
                    "localmax_v2_release",
                ])
                / (1024**3),
                3,
            ),
            "cuda_available": cuda_available,
            "cuda_version": cuda_version,
            "gpu": gpu_name,
            "gpu_memory_gb": gpu_memory_gb,
            "estimated_data_size_gb": estimated_data_size_gb,
            "estimated_training_artifacts_gb": estimated_training_artifacts_gb,
            "maximum_safe_data_budget_gb": round(max_safe_data_budget_gb, 2),
            "maximum_safe_training_budget_gb": 2.0,
            "estimated_training_time": "measured by benchmark_training_throughput.py",
            "projected_completion_time": "computed after throughput benchmark",
            "selected_execution_tier": selected_tier,
            "required_modules": modules,
            "duration_seconds": round(time.perf_counter() - started, 3),
            "notes": [
                "LocalMax V2 targets 100M GPT-2 tokens per dataset and 1M tokens_seen per core run.",
                "The selected tier is conservative for an 8GB RTX 4060 Laptop GPU.",
            ],
        },
    )
    write_report(report, "localmax_v2_environment_report", "LocalMax V2 Environment Report")
    print(json.dumps({"localmax_v2_environment_ready": ready, "selected_tier": selected_tier, "disk_free_gb": free_gb}))


if __name__ == "__main__":
    main()
