from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import TrainingConfig, VALID_TRAINING_SCOPES
from .manifest import MANIFEST_VERSION
from tokenization.manifest import sha256_file_variants


class TrainingManifestError(ValueError):
    pass


def validate_training_config(config: TrainingConfig) -> None:
    if config.scope not in VALID_TRAINING_SCOPES:
        raise ValueError(f"invalid training scope: {config.scope}")
    if config.scope == "smoke" and config.smoke_only is not True:
        raise ValueError("smoke training scope must set smoke_only=true")
    if config.scope in {"main_protocol", "level2_protocol", "level3_heavy_protocol"} and config.smoke_only:
        raise ValueError("protocol scopes must not be labeled smoke_only")
    protocol_scope = config.scope in {"main_protocol", "level2_protocol", "level3_heavy_protocol"}
    if config.max_steps < 0:
        raise ValueError("max_steps must be non-negative")
    if config.batch_size < 1 and not protocol_scope:
        raise ValueError("batch_size must be >= 1")
    if config.learning_rate <= 0:
        raise ValueError("learning_rate must be positive")
    if config.eval_interval < 1:
        raise ValueError("eval_interval must be >= 1")


def _error(message: str) -> None:
    raise TrainingManifestError(message)


def _resolve(path: str, root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root / value


def _validate_hash_field(manifest: dict[str, Any], root: Path, path_field: str, hash_field: str) -> None:
    path = str(manifest.get(path_field, ""))
    expected = str(manifest.get(hash_field, ""))
    if not path and not expected:
        return
    if not path:
        _error(f"{path_field} is empty but {hash_field} is set")
    resolved = _resolve(path, root)
    if not resolved.exists():
        _error(f"{path_field} does not exist: {path}")
    if expected not in sha256_file_variants(resolved):
        _error(f"{hash_field} does not match {path_field}")


def validate_training_manifest(manifest: dict[str, Any], root: Path) -> None:
    required = [
        "manifest_version",
        "experiment_name",
        "scope",
        "smoke_only",
        "dataset_path",
        "dataset_manifest_path",
        "dataset_manifest_hash",
        "tokenizer_manifest_path",
        "tokenizer_manifest_hash",
        "filter_manifest_path",
        "filter_manifest_hash",
        "model_config",
        "parameter_count",
        "scale_class",
        "seed",
        "max_steps",
        "batch_size",
        "learning_rate",
        "tokens_seen",
        "train_loss_final",
        "validation_loss",
        "validation_ppl",
        "metrics_path",
        "metrics_hash",
        "checkpoint_path",
        "checkpoint_hash",
        "checkpoint_manifest_path",
        "checkpoint_manifest_hash",
        "created_at",
        "completed",
        "implemented_but_not_run",
        "notes",
    ]
    missing = [field for field in required if field not in manifest]
    if missing:
        _error(f"training manifest missing fields: {', '.join(missing)}")
    if manifest["manifest_version"] != MANIFEST_VERSION:
        _error(f"unsupported manifest_version: {manifest['manifest_version']}")
    if manifest["scope"] not in VALID_TRAINING_SCOPES:
        _error(f"invalid scope: {manifest['scope']}")
    if manifest["scope"] == "smoke" and manifest["smoke_only"] is not True:
        _error("smoke training manifest must set smoke_only=true")
    if manifest["scope"] in {"main_protocol", "level2_protocol", "level3_heavy_protocol"}:
        if manifest["completed"] is True:
            _error("protocol-only training manifest cannot claim completed=true")
        if manifest["implemented_but_not_run"] is not True:
            _error("protocol-only training manifest must set implemented_but_not_run=true")
    if manifest["completed"] is False:
        for metric_field in ["train_loss_final", "validation_loss", "validation_ppl"]:
            if manifest.get(metric_field) not in {"", None}:
                _error("completed=false manifest cannot contain final metrics")
    _validate_hash_field(manifest, root, "dataset_manifest_path", "dataset_manifest_hash")
    _validate_hash_field(manifest, root, "tokenizer_manifest_path", "tokenizer_manifest_hash")
    _validate_hash_field(manifest, root, "filter_manifest_path", "filter_manifest_hash")
    _validate_hash_field(manifest, root, "metrics_path", "metrics_hash")
    _validate_hash_field(manifest, root, "checkpoint_path", "checkpoint_hash")
    _validate_hash_field(manifest, root, "checkpoint_manifest_path", "checkpoint_manifest_hash")
    metrics_path = str(manifest.get("metrics_path", ""))
    if metrics_path:
        metrics = json.loads(_resolve(metrics_path, root).read_text(encoding="utf-8"))
        if manifest["scope"] == "smoke" and metrics.get("smoke_only") is not True:
            _error("smoke metrics must set smoke_only=true")


def assert_training_outputs_not_in_main_results(root: Path) -> None:
    forbidden = "training_step5"
    for path in [
        root / "artifacts" / "tables" / "main_results.csv",
        root / "artifacts" / "stats" / "main_results.csv",
        root / "artifacts" / "cross_dataset" / "cross_dataset_results.csv",
    ]:
        if path.exists() and forbidden in path.read_text(encoding="utf-8", errors="ignore"):
            _error(f"Step 5 smoke output leaked into {path.relative_to(root).as_posix()}")
