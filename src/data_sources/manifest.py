from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .records import DatasetRecord
from .token_budget import estimate_text_tokens, parse_token_budget

MANIFEST_VERSION = "step2.dataset_manifest.v1"
VALID_SOURCE_KINDS = {"local", "hf_streaming", "hf_dataset", "fixture", "optional_remote"}
VALID_SCOPES = {"smoke", "sample", "main", "heavy", "implemented_but_not_run"}
VALID_TOKEN_COUNTERS = {"whitespace", "character", "unknown", "future_bpe"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def project_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def create_manifest(
    *,
    root: Path,
    dataset_name: str,
    dataset_version: str,
    split: str,
    source_kind: str,
    scope: str,
    token_budget_requested: str | int | None,
    actual_estimated_tokens: int,
    token_counter_type: str,
    num_documents: int,
    sampling_seed: int,
    shuffle: bool,
    allow_fallback: bool,
    fallback_used: bool,
    smoke_only: bool,
    implemented_but_not_run: bool,
    output_path: Path | None,
    license_note: str,
    loader_name: str,
    loader_version: str,
    upstream_url_or_id: str,
    notes: str = "",
) -> dict[str, Any]:
    token_budget_numeric = parse_token_budget(token_budget_requested)
    data_hash = ""
    output_value = ""
    if output_path is not None:
        output_value = project_relative(output_path, root)
        if output_path.exists():
            data_hash = sha256_file(output_path)

    return {
        "manifest_version": MANIFEST_VERSION,
        "dataset_name": dataset_name,
        "dataset_version": dataset_version,
        "split": split,
        "source_kind": source_kind,
        "scope": scope,
        "token_budget_requested": "full" if token_budget_requested is None else str(token_budget_requested),
        "token_budget_numeric": token_budget_numeric,
        "actual_estimated_tokens": actual_estimated_tokens,
        "token_counter_type": token_counter_type,
        "num_documents": num_documents,
        "sampling_seed": sampling_seed,
        "shuffle": bool(shuffle),
        "allow_fallback": bool(allow_fallback),
        "fallback_used": bool(fallback_used),
        "smoke_only": bool(smoke_only),
        "implemented_but_not_run": bool(implemented_but_not_run),
        "data_hash": data_hash,
        "output_path": output_value,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "license_note": license_note,
        "loader_name": loader_name,
        "loader_version": loader_version,
        "upstream_url_or_id": upstream_url_or_id,
        "notes": notes,
    }


def manifest_for_records(
    *,
    root: Path,
    dataset_name: str,
    dataset_version: str,
    split: str,
    source_kind: str,
    scope: str,
    token_budget_requested: str | int | None,
    records: list[DatasetRecord],
    token_counter_type: str,
    sampling_seed: int,
    shuffle: bool,
    allow_fallback: bool,
    fallback_used: bool,
    smoke_only: bool,
    implemented_but_not_run: bool,
    output_path: Path | None,
    license_note: str,
    loader_name: str,
    loader_version: str,
    upstream_url_or_id: str,
    notes: str = "",
) -> dict[str, Any]:
    actual_tokens = sum(estimate_text_tokens(record.text, token_counter_type) for record in records)
    return create_manifest(
        root=root,
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        split=split,
        source_kind=source_kind,
        scope=scope,
        token_budget_requested=token_budget_requested,
        actual_estimated_tokens=actual_tokens,
        token_counter_type=token_counter_type,
        num_documents=len(records),
        sampling_seed=sampling_seed,
        shuffle=shuffle,
        allow_fallback=allow_fallback,
        fallback_used=fallback_used,
        smoke_only=smoke_only,
        implemented_but_not_run=implemented_but_not_run,
        output_path=output_path,
        license_note=license_note,
        loader_name=loader_name,
        loader_version=loader_version,
        upstream_url_or_id=upstream_url_or_id,
        notes=notes,
    )


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
