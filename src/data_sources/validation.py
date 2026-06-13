from __future__ import annotations

from pathlib import Path
from typing import Any

from .manifest import (
    MANIFEST_VERSION,
    VALID_SCOPES,
    VALID_SOURCE_KINDS,
    VALID_TOKEN_COUNTERS,
    sha256_file,
)


class DatasetManifestError(ValueError):
    pass


def _error(message: str) -> None:
    raise DatasetManifestError(message)


def _resolve_output_path(manifest: dict[str, Any], root: Path | None) -> Path | None:
    output = str(manifest.get("output_path") or "")
    if not output:
        return None
    path = Path(output)
    if path.is_absolute():
        return path
    return (root or Path.cwd()) / path


def validate_scope_consistency(manifest: dict[str, Any]) -> None:
    scope = str(manifest.get("scope", ""))
    source_kind = str(manifest.get("source_kind", ""))
    if scope not in VALID_SCOPES:
        _error(f"invalid scope: {scope}")
    if source_kind not in VALID_SOURCE_KINDS:
        _error(f"invalid source_kind: {source_kind}")
    if scope in {"main", "heavy"} and manifest.get("allow_fallback") is not False:
        _error("main/heavy scope must set allow_fallback=false")
    if scope in {"main", "heavy"} and manifest.get("fallback_used") is True:
        _error("fallback_used=true cannot enter main/heavy")
    if scope == "smoke" and manifest.get("smoke_only") is not True:
        _error("smoke scope must set smoke_only=true")
    if manifest.get("implemented_but_not_run") is True and manifest.get("output_path"):
        _error("implemented-but-not-run manifest must not claim an output_path")
    if scope == "implemented_but_not_run" and manifest.get("implemented_but_not_run") is not True:
        _error("implemented_but_not_run scope must set implemented_but_not_run=true")


def validate_output_hash(manifest: dict[str, Any], root: Path | None = None) -> None:
    output_path = _resolve_output_path(manifest, root)
    if output_path is None:
        if manifest.get("data_hash"):
            _error("data_hash cannot be set without output_path")
        return
    if not output_path.exists():
        _error(f"output_path does not exist: {output_path}")
    expected = str(manifest.get("data_hash") or "")
    if not expected:
        _error("manifest with output_path must include data_hash")
    actual = sha256_file(output_path)
    if actual != expected:
        _error(f"data_hash mismatch for {output_path}: expected {expected}, got {actual}")


def validate_token_budget_consistency(manifest: dict[str, Any]) -> None:
    counter_type = str(manifest.get("token_counter_type", ""))
    if counter_type not in VALID_TOKEN_COUNTERS:
        _error(f"invalid token_counter_type: {counter_type}")
    numeric = manifest.get("token_budget_numeric")
    actual = int(manifest.get("actual_estimated_tokens") or 0)
    if numeric is not None and actual > int(numeric):
        _error(f"actual_estimated_tokens {actual} exceeds token_budget_numeric {numeric}")
    if counter_type == "future_bpe" and actual:
        _error("future_bpe token counter cannot be used for current proxy counts")


def validate_no_fallback_for_main(manifest: dict[str, Any]) -> None:
    if str(manifest.get("scope")) in {"main", "heavy"}:
        if manifest.get("allow_fallback") is not False:
            _error("main/heavy manifest allows fallback")
        if manifest.get("fallback_used") is True:
            _error("main/heavy manifest used fallback")


def validate_manifest(manifest: dict[str, Any], root: Path | None = None) -> None:
    required = [
        "manifest_version",
        "dataset_name",
        "dataset_version",
        "split",
        "source_kind",
        "scope",
        "token_budget_requested",
        "token_budget_numeric",
        "actual_estimated_tokens",
        "token_counter_type",
        "num_documents",
        "sampling_seed",
        "shuffle",
        "allow_fallback",
        "fallback_used",
        "smoke_only",
        "implemented_but_not_run",
        "data_hash",
        "output_path",
        "created_at",
        "license_note",
        "loader_name",
        "loader_version",
        "upstream_url_or_id",
        "notes",
    ]
    missing = [field for field in required if field not in manifest]
    if missing:
        _error(f"manifest missing required fields: {', '.join(missing)}")
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        _error(f"unsupported manifest_version: {manifest.get('manifest_version')}")
    validate_scope_consistency(manifest)
    validate_no_fallback_for_main(manifest)
    validate_token_budget_consistency(manifest)
    validate_output_hash(manifest, root)
