from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import EvaluationConfig
from .io import project_relative, resolve_path
from .schema import MANIFEST_VERSION


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_optional(path: str, root: Path) -> str:
    if not path:
        return ""
    resolved = resolve_path(path, root)
    return sha256_file(resolved) if resolved.exists() else ""


def create_evaluation_manifest(
    *,
    config: EvaluationConfig,
    root: Path,
    metrics_path: Path,
    report_path: Path,
    completed: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "manifest_version": MANIFEST_VERSION,
        "evaluation_name": config.evaluation_name,
        "evaluation_type": config.evaluation_type,
        "scope": config.scope,
        "smoke_only": bool(config.smoke_only),
        "protocol_only": bool(config.protocol_only),
        "completed": bool(completed),
        "method_name": config.method_name,
        "dataset_name": config.dataset_name,
        "input_artifact_path": project_relative(config.input_artifact_path, root),
        "input_artifact_hash": _hash_optional(config.input_artifact_path, root),
        "input_manifest_path": project_relative(config.input_manifest_path, root),
        "input_manifest_hash": _hash_optional(config.input_manifest_path, root),
        "training_manifest_path": project_relative(config.training_manifest_path, root),
        "training_manifest_hash": _hash_optional(config.training_manifest_path, root),
        "filter_manifest_path": project_relative(config.filter_manifest_path, root),
        "filter_manifest_hash": _hash_optional(config.filter_manifest_path, root),
        "tokenizer_manifest_path": project_relative(config.tokenizer_manifest_path, root),
        "tokenizer_manifest_hash": _hash_optional(config.tokenizer_manifest_path, root),
        "metrics_path": project_relative(metrics_path, root),
        "metrics_hash": sha256_file(metrics_path),
        "report_path": project_relative(report_path, root),
        "report_hash": sha256_file(report_path),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "no_main_results_written": True,
        "effectiveness_claim_allowed": False,
        "notes": notes,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
