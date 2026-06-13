from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tokenization.manifest import sha256_file

MANIFEST_VERSION = "step5.training_manifest.v1"


def project_relative(path: str | Path, root: Path) -> str:
    if not path:
        return ""
    value = Path(path)
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return value.as_posix()


def _hash_optional(path: str | Path, root: Path) -> str:
    if not path:
        return ""
    value = Path(path)
    resolved = value if value.is_absolute() else root / value
    return sha256_file(resolved) if resolved.exists() else ""


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def create_training_manifest(
    *,
    config,
    model_config,
    root: Path,
    metrics_path: Path,
    metrics: dict[str, Any],
    checkpoint_info: dict[str, str],
    data_summary: dict[str, Any],
    completed: bool,
    implemented_but_not_run: bool,
) -> dict[str, Any]:
    train_loss_final = metrics.get("train_loss_final") if completed else None
    validation_loss = metrics.get("validation_loss") if completed else None
    validation_ppl = metrics.get("validation_ppl") if completed else None
    return {
        "manifest_version": MANIFEST_VERSION,
        "experiment_name": config.experiment_name,
        "scope": config.scope,
        "smoke_only": bool(config.smoke_only),
        "dataset_path": project_relative(config.dataset_path, root),
        "dataset_manifest_path": project_relative(config.dataset_manifest_path, root),
        "dataset_manifest_hash": _hash_optional(config.dataset_manifest_path, root),
        "tokenizer_manifest_path": project_relative(config.tokenizer_manifest_path, root),
        "tokenizer_manifest_hash": _hash_optional(config.tokenizer_manifest_path, root),
        "filter_manifest_path": project_relative(config.filter_manifest_path, root),
        "filter_manifest_hash": _hash_optional(config.filter_manifest_path, root),
        "model_config": model_config.to_dict(),
        "parameter_count": model_config.parameter_count,
        "scale_class": model_config.scale_class,
        "seed": config.seed,
        "max_steps": config.max_steps,
        "batch_size": config.batch_size,
        "learning_rate": config.learning_rate,
        "tokens_seen": metrics.get("tokens_seen", 0) if completed else 0,
        "train_loss_final": train_loss_final,
        "validation_loss": validation_loss,
        "validation_ppl": validation_ppl,
        "metrics_path": project_relative(metrics_path, root) if completed else "",
        "metrics_hash": sha256_file(metrics_path) if completed and metrics_path.exists() else "",
        "checkpoint_path": checkpoint_info.get("checkpoint_path", ""),
        "checkpoint_hash": checkpoint_info.get("checkpoint_hash", ""),
        "checkpoint_manifest_path": checkpoint_info.get("checkpoint_manifest_path", ""),
        "checkpoint_manifest_hash": checkpoint_info.get("checkpoint_manifest_hash", ""),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "completed": bool(completed),
        "implemented_but_not_run": bool(implemented_but_not_run),
        "data_summary": data_summary,
        "notes": config.notes,
    }
