from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .manifest import MANIFEST_VERSION, VALID_SCOPES, sha256_file


class FilterManifestError(ValueError):
    pass


REQUIRED_OUTPUT_FILES = {
    "selected_doc_ids.jsonl",
    "decisions.jsonl",
    "scores.jsonl",
    "keep_rate_report.json",
    "risk_report.json",
    "diversity_report.json",
    "cost_report.json",
}


def _error(message: str) -> None:
    raise FilterManifestError(message)


def _resolve(path: str, root: Path) -> Path:
    value = Path(path)
    return value if value.is_absolute() else root / value


def _check_rate(name: str, value: Any) -> None:
    if not isinstance(value, (int, float)):
        _error(f"{name} must be numeric")
    if not 0 <= float(value) <= 1:
        _error(f"{name} must be in [0, 1]")


def validate_filter_manifest(manifest: dict[str, Any], root: Path) -> None:
    required = [
        "manifest_version",
        "filter_name",
        "filter_type",
        "scope",
        "dataset_name",
        "dataset_manifest_path",
        "dataset_manifest_hash",
        "tokenizer_manifest_path",
        "tokenizer_manifest_hash",
        "target_keep_rate",
        "actual_document_keep_rate",
        "actual_token_keep_rate",
        "input_docs",
        "kept_docs",
        "input_estimated_tokens",
        "kept_estimated_tokens",
        "token_counter_type",
        "seed",
        "allow_proxy",
        "proxy_used",
        "external_dependency",
        "external_dependency_available",
        "smoke_only",
        "implemented_but_not_run",
        "created_at",
        "output_hashes",
        "notes",
    ]
    missing = [field for field in required if field not in manifest]
    if missing:
        _error(f"filter manifest missing required fields: {', '.join(missing)}")
    if manifest["manifest_version"] != MANIFEST_VERSION:
        _error(f"unsupported manifest_version: {manifest['manifest_version']}")
    if manifest["scope"] not in VALID_SCOPES:
        _error(f"invalid scope: {manifest['scope']}")
    if manifest["scope"] == "smoke" and manifest.get("smoke_only") is not True:
        _error("smoke filter output must set smoke_only=true")
    _check_rate("actual_document_keep_rate", manifest["actual_document_keep_rate"])
    _check_rate("actual_token_keep_rate", manifest["actual_token_keep_rate"])
    if manifest.get("official_reproduction") is True:
        _error("Step 4 manifests must not claim official reproduction")
    filter_type = str(manifest.get("filter_type", ""))
    if (
        "proxy" in filter_type
        or filter_type in {"ccnet_style_proxy", "classifier_quality_proxy", "embedding_diversity_proxy"}
    ) and manifest.get("proxy_used") is not True:
        _error(f"proxy filter must set proxy_used=true: {filter_type}")
    if manifest.get("implemented_but_not_run") is True and manifest.get("kept_docs", 0):
        _error("implemented_but_not_run manifest cannot claim kept docs")
    dataset_path = _resolve(str(manifest["dataset_manifest_path"]), root)
    tokenizer_path = _resolve(str(manifest["tokenizer_manifest_path"]), root)
    if not dataset_path.exists():
        _error(f"dataset manifest missing: {dataset_path}")
    if not tokenizer_path.exists():
        _error(f"tokenizer manifest missing: {tokenizer_path}")
    if sha256_file(dataset_path) != manifest["dataset_manifest_hash"]:
        _error("dataset_manifest_hash does not match file")
    if sha256_file(tokenizer_path) != manifest["tokenizer_manifest_hash"]:
        _error("tokenizer_manifest_hash does not match file")
    hashes = manifest.get("output_hashes")
    if not isinstance(hashes, dict):
        _error("output_hashes must be an object")
    missing_outputs = REQUIRED_OUTPUT_FILES - set(hashes)
    if missing_outputs:
        _error(f"output_hashes missing files: {', '.join(sorted(missing_outputs))}")
    for name, info in hashes.items():
        if not isinstance(info, dict) or "path" not in info or "sha256" not in info:
            _error(f"invalid output hash entry: {name}")
        path = _resolve(str(info["path"]), root)
        if not path.exists():
            _error(f"output file missing: {path}")
        if sha256_file(path) != info["sha256"]:
            _error(f"output hash mismatch: {path}")
    keep_rate_report_path = _resolve(str(hashes["keep_rate_report.json"]["path"]), root)
    keep_rate_report = json.loads(keep_rate_report_path.read_text(encoding="utf-8"))
    for field in ["document_keep_rate", "token_keep_rate", "token_counter_type"]:
        if field not in keep_rate_report:
            _error(f"keep_rate_report missing {field}")


def validate_filter_output_dir(path: Path, root: Path) -> None:
    manifest_path = path / "filter_manifest.json"
    if not manifest_path.exists():
        _error(f"filter_manifest.json missing in {path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    validate_filter_manifest(manifest, root)
