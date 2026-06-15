from __future__ import annotations

import platform
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.data.splitting import SplitManifest
from dataaudit_lm.integrity.hashing import sha256_json


def build_dataset_manifest(
    *,
    dataset_repository: str,
    config: str,
    revision: str,
    records: list[DataRecord],
    split_manifest: SplitManifest | None = None,
    tokenizer_revision: str = "gpt2",
    streaming_parameters: dict[str, Any] | None = None,
    license_note: str = "recorded for audit; verify upstream license before redistribution",
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "manifest_version": "dataaudit_lm_dataset_manifest_v1",
        "dataset_repository": dataset_repository,
        "config": config,
        "revision": revision,
        "acquisition_date": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "python_version": platform.python_version(),
        "tokenizer_revision": tokenizer_revision,
        "streaming_parameters": dict(streaming_parameters or {}),
        "record_count": len(records),
        "token_count": sum(record.token_count for record in records),
        "raw_ingestion_policy": "retain_all_upstream_records_no_content_dedup",
        "content_hashes": sorted({record.content_sha256 for record in records}),
        "source_fingerprint": sha256_json([record.to_dict() for record in records]),
        "license_note": license_note,
    }
    if split_manifest is not None:
        payload["split_manifest"] = asdict(split_manifest)
    payload["manifest_hash"] = sha256_json(payload)
    return payload
