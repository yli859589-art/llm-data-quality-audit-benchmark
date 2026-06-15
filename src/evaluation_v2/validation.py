from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .manifest import sha256_file_variants
from .schema import MANIFEST_VERSION, PROTECTED_RESULT_FILES, PROTOCOL_SCOPES, VALID_EVALUATION_TYPES, VALID_SCOPES


class EvaluationManifestError(ValueError):
    pass


REQUIRED_FIELDS = [
    "manifest_version",
    "evaluation_name",
    "evaluation_type",
    "scope",
    "smoke_only",
    "protocol_only",
    "completed",
    "method_name",
    "dataset_name",
    "input_artifact_path",
    "input_artifact_hash",
    "input_manifest_path",
    "input_manifest_hash",
    "training_manifest_path",
    "training_manifest_hash",
    "filter_manifest_path",
    "filter_manifest_hash",
    "tokenizer_manifest_path",
    "tokenizer_manifest_hash",
    "metrics_path",
    "metrics_hash",
    "report_path",
    "report_hash",
    "created_at",
    "no_main_results_written",
    "effectiveness_claim_allowed",
    "notes",
]


def _error(message: str) -> None:
    raise EvaluationManifestError(message)


def _resolve(path: str, root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root / value


def _validate_hash_pair(manifest: dict[str, Any], root: Path, path_field: str, hash_field: str) -> None:
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


def validate_evaluation_manifest(manifest: dict[str, Any], root: Path) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in manifest]
    if missing:
        _error("evaluation manifest missing fields: " + ", ".join(missing))
    if manifest["manifest_version"] != MANIFEST_VERSION:
        _error(f"unsupported manifest_version: {manifest['manifest_version']}")
    if manifest["evaluation_type"] not in VALID_EVALUATION_TYPES:
        _error(f"invalid evaluation_type: {manifest['evaluation_type']}")
    if manifest["scope"] not in VALID_SCOPES:
        _error(f"invalid scope: {manifest['scope']}")
    if manifest["scope"] == "smoke" and manifest["smoke_only"] is not True:
        _error("smoke evaluation manifest must set smoke_only=true")
    if manifest["scope"] in PROTOCOL_SCOPES and manifest["protocol_only"] is not True:
        _error("protocol evaluation manifest must set protocol_only=true")
    if manifest["evaluation_type"] == "downstream_protocol" and manifest["completed"] is not False:
        _error("downstream protocol output must not claim completed=true")
    if manifest["no_main_results_written"] is not True:
        _error("evaluation manifest must set no_main_results_written=true")
    if manifest["effectiveness_claim_allowed"] is not False:
        _error("Step 7 evaluation manifest must set effectiveness_claim_allowed=false")
    for path_field, hash_field in [
        ("input_artifact_path", "input_artifact_hash"),
        ("input_manifest_path", "input_manifest_hash"),
        ("training_manifest_path", "training_manifest_hash"),
        ("filter_manifest_path", "filter_manifest_hash"),
        ("tokenizer_manifest_path", "tokenizer_manifest_hash"),
        ("metrics_path", "metrics_hash"),
        ("report_path", "report_hash"),
    ]:
        _validate_hash_pair(manifest, root, path_field, hash_field)
    metrics = json.loads(_resolve(str(manifest["metrics_path"]), root).read_text(encoding="utf-8"))
    forbidden_truthy = [
        "effectiveness_claim_allowed",
        "pareto_improvement_claim_allowed",
        "ranking_stability_claim_allowed",
    ]
    for field in forbidden_truthy:
        if metrics.get(field) is True:
            _error(f"metrics file contains unsupported truthy claim field: {field}")
    if manifest["completed"] is False and metrics.get("final_metrics") is not None:
        _error("completed=false evaluation cannot contain final_metrics")


def assert_evaluation_outputs_not_in_main_results(root: Path) -> None:
    forbidden = ["evaluation_step7", "evaluation_manifest", "downstream_protocol_matrix"]
    for relative in PROTECTED_RESULT_FILES:
        path = root / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden:
            if token in text:
                _error(f"Step 7 evaluation output leaked into {relative}")
