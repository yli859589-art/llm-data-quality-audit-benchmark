from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import FilterConfig, FilterResult

MANIFEST_VERSION = "step4.filter_manifest.v1"
VALID_SCOPES = {"smoke", "sample", "main_protocol", "implemented_but_not_run"}


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_relative(path: str | Path, root: Path) -> str:
    value = Path(path)
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return value.as_posix()


def _manifest_hash(path: str, root: Path) -> str:
    if not path:
        return ""
    value = root / path if not Path(path).is_absolute() else Path(path)
    return sha256_file(value) if value.exists() else ""


def create_filter_manifest(
    *,
    config: FilterConfig,
    result: FilterResult,
    root: Path,
    output_dir: Path,
    output_hashes: dict[str, dict[str, str]],
    proxy_used: bool,
    external_dependency: str,
    external_dependency_available: bool,
    implemented_but_not_run: bool,
    historical_baseline: bool,
    official_reproduction: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "manifest_version": MANIFEST_VERSION,
        "filter_name": config.filter_name,
        "filter_type": result.filter_type,
        "scope": config.scope,
        "dataset_name": config.dataset_name,
        "dataset_manifest_path": project_relative(config.dataset_manifest_path, root),
        "dataset_manifest_hash": _manifest_hash(config.dataset_manifest_path, root),
        "tokenizer_manifest_path": project_relative(config.tokenizer_manifest_path, root),
        "tokenizer_manifest_hash": _manifest_hash(config.tokenizer_manifest_path, root),
        "target_keep_rate": config.target_keep_rate,
        "actual_document_keep_rate": result.document_keep_rate,
        "actual_token_keep_rate": result.token_keep_rate,
        "input_docs": result.input_docs,
        "kept_docs": result.kept_docs,
        "input_estimated_tokens": result.input_estimated_tokens,
        "kept_estimated_tokens": result.kept_estimated_tokens,
        "token_counter_type": config.token_counter_type,
        "seed": config.seed,
        "allow_proxy": config.allow_proxy,
        "proxy_used": bool(proxy_used),
        "external_dependency": external_dependency,
        "external_dependency_available": bool(external_dependency_available),
        "smoke_only": bool(config.smoke_only),
        "implemented_but_not_run": bool(implemented_but_not_run),
        "historical_baseline": bool(historical_baseline),
        "official_reproduction": bool(official_reproduction),
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "output_dir": project_relative(output_dir, root),
        "output_hashes": output_hashes,
        "notes": notes,
    }
