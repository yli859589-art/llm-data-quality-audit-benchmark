from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .manifest import sha256_file_variants
from .schema import (
    MANIFEST_VERSION,
    PROTECTED_RESULT_FILES,
    PROTOCOL_SCOPES,
    VALID_ANALYSIS_TYPES,
    VALID_EVIDENCE_SUFFICIENCY,
    VALID_SCOPES,
)


class MechanismManifestError(ValueError):
    pass


REQUIRED_FIELDS = [
    "manifest_version",
    "analysis_name",
    "analysis_type",
    "scope",
    "smoke_only",
    "protocol_only",
    "completed",
    "dataset_name",
    "methods",
    "input_artifact_paths",
    "input_artifact_hashes",
    "input_manifest_paths",
    "input_manifest_hashes",
    "training_manifest_paths",
    "training_manifest_hashes",
    "filter_manifest_paths",
    "filter_manifest_hashes",
    "evaluation_manifest_paths",
    "evaluation_manifest_hashes",
    "tokenizer_manifest_paths",
    "tokenizer_manifest_hashes",
    "diagnostic_table_path",
    "diagnostic_table_hash",
    "diagnostic_report_path",
    "diagnostic_report_hash",
    "figure_paths",
    "figure_hashes",
    "evidence_sufficiency",
    "insufficient_evidence",
    "claim_allowed",
    "main_results_modified",
    "created_at",
    "notes",
]


def _error(message: str) -> None:
    raise MechanismManifestError(message)


def _resolve(path: str, root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root / value


def _validate_hash(path_value: str, expected: str, root: Path, field_name: str) -> None:
    if not path_value:
        _error(f"{field_name} path is empty")
    resolved = _resolve(path_value, root)
    if not resolved.exists():
        _error(f"{field_name} path does not exist: {path_value}")
    if expected not in sha256_file_variants(resolved):
        _error(f"{field_name} hash mismatch for {path_value}")


def _validate_hash_map(paths: list[Any], hashes: dict[str, Any], root: Path, field_name: str) -> None:
    for item in paths:
        path_value = str(item)
        expected = str(hashes.get(path_value, ""))
        _validate_hash(path_value, expected, root, field_name)


def _validate_json_claim_flags(path: Path) -> None:
    if path.suffix.lower() != ".json":
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    forbidden_truthy = [
        "claim_allowed",
        "effectiveness_claim_allowed",
        "full_scale_mechanism_conclusion_allowed",
        "pareto_improvement_claim_allowed",
        "urd_effectiveness_verified",
    ]
    if isinstance(payload, dict):
        for field in forbidden_truthy:
            if payload.get(field) is True:
                _error(f"extra JSON output contains unsupported truthy claim field: {field}")


def validate_mechanism_manifest(manifest: dict[str, Any], root: Path) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in manifest]
    if missing:
        _error("mechanism manifest missing fields: " + ", ".join(missing))
    if manifest["manifest_version"] != MANIFEST_VERSION:
        _error(f"unsupported manifest_version: {manifest['manifest_version']}")
    if manifest["analysis_type"] not in VALID_ANALYSIS_TYPES:
        _error(f"invalid analysis_type: {manifest['analysis_type']}")
    if manifest["scope"] not in VALID_SCOPES:
        _error(f"invalid scope: {manifest['scope']}")
    if manifest["evidence_sufficiency"] not in VALID_EVIDENCE_SUFFICIENCY:
        _error(f"invalid evidence_sufficiency: {manifest['evidence_sufficiency']}")
    if manifest["scope"] == "smoke" and manifest["smoke_only"] is not True:
        _error("smoke mechanism manifest must set smoke_only=true")
    if manifest["scope"] in PROTOCOL_SCOPES and manifest["protocol_only"] is not True:
        _error("protocol mechanism manifest must set protocol_only=true")
    if manifest["claim_allowed"] is not False:
        _error("Step 8 mechanism manifest must set claim_allowed=false")
    if manifest.get("effectiveness_claim_allowed") is not False:
        _error("Step 8 mechanism manifest must set effectiveness_claim_allowed=false")
    if manifest.get("full_scale_mechanism_conclusion_allowed") is not False:
        _error("Step 8 mechanism manifest must disable full-scale mechanism conclusions")
    if manifest["main_results_modified"] is not False:
        _error("Step 8 mechanism manifest must set main_results_modified=false")
    if manifest["evidence_sufficiency"] in {"protocol_only", "smoke_diagnostic_only", "insufficient"}:
        if manifest["insufficient_evidence"] is not True:
            _error("limited Step 8 evidence must set insufficient_evidence=true")
    _validate_hash(str(manifest["diagnostic_table_path"]), str(manifest["diagnostic_table_hash"]), root, "diagnostic_table")
    _validate_hash(str(manifest["diagnostic_report_path"]), str(manifest["diagnostic_report_hash"]), root, "diagnostic_report")
    for paths_field, hashes_field in [
        ("input_artifact_paths", "input_artifact_hashes"),
        ("input_manifest_paths", "input_manifest_hashes"),
        ("training_manifest_paths", "training_manifest_hashes"),
        ("filter_manifest_paths", "filter_manifest_hashes"),
        ("evaluation_manifest_paths", "evaluation_manifest_hashes"),
        ("tokenizer_manifest_paths", "tokenizer_manifest_hashes"),
        ("figure_paths", "figure_hashes"),
    ]:
        _validate_hash_map(list(manifest.get(paths_field, [])), dict(manifest.get(hashes_field, {})), root, paths_field)
    for path_value in manifest.get("extra_output_paths", []):
        _validate_hash(
            str(path_value),
            str(manifest.get("extra_output_hashes", {}).get(path_value, "")),
            root,
            "extra_output",
        )
        _validate_json_claim_flags(_resolve(str(path_value), root))


def assert_mechanism_outputs_not_in_main_results(root: Path) -> None:
    forbidden = ["analysis_step8", "mechanism_manifest", "proxy_utility_diagnostics", "pareto_mechanism"]
    for relative in PROTECTED_RESULT_FILES:
        path = root / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for token in forbidden:
            if token in text:
                _error(f"Step 8 mechanism output leaked into {relative}")
