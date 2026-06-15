from __future__ import annotations

from dataaudit_lm.integrity.hashing import sha256_json


def build_lineage(
    *,
    data_manifest_hash: str,
    filter_manifest_hash: str,
    sample_manifest_hash: str,
    initialization_fingerprint: str,
    training_config: dict[str, object],
) -> dict[str, object]:
    payload = {
        "data_manifest_hash": data_manifest_hash,
        "filter_manifest_hash": filter_manifest_hash,
        "sample_manifest_hash": sample_manifest_hash,
        "initialization_fingerprint": initialization_fingerprint,
        "training_config": training_config,
        "warm_start": False,
    }
    payload["lineage_hash"] = sha256_json(payload)
    return payload
