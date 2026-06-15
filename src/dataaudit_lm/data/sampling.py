from __future__ import annotations

from dataclasses import dataclass

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.integrity.hashing import sha256_json, stable_hash_int


@dataclass(frozen=True)
class SampleManifest:
    sampling_algorithm: str
    sampling_seed: int
    selected_document_ids: list[str]
    sampled_token_count: int
    selected_corpus_hash: str
    sample_manifest_hash: str


def corpus_wide_token_sample(
    records: list[DataRecord],
    *,
    token_budget: int,
    seed: int,
) -> tuple[list[DataRecord], SampleManifest]:
    """Sample from the full selected corpus by stable hash ranking, not shard prefix order."""
    if token_budget <= 0:
        raise ValueError("token_budget must be positive")
    ranked = sorted(
        records,
        key=lambda record: (
            stable_hash_int(f"{seed}:{record.record_id}:{record.content_sha256}"),
            record.record_id,
        ),
    )
    selected: list[DataRecord] = []
    total = 0
    for record in ranked:
        if selected and total + record.token_count > token_budget:
            continue
        if not selected or total + record.token_count <= token_budget:
            selected.append(record)
            total += record.token_count
        if total >= token_budget:
            break
    corpus_hash = sha256_json(
        [record.to_dict() for record in sorted(records, key=lambda item: item.record_id)]
    )
    payload = {
        "algorithm": "corpus_wide_hash_ranked_token_sample_v1",
        "corpus_hash": corpus_hash,
        "ids": [record.record_id for record in selected],
        "seed": seed,
        "tokens": total,
    }
    manifest = SampleManifest(
        sampling_algorithm="corpus_wide_hash_ranked_token_sample_v1",
        sampling_seed=seed,
        selected_document_ids=[record.record_id for record in selected],
        sampled_token_count=total,
        selected_corpus_hash=corpus_hash,
        sample_manifest_hash=sha256_json(payload),
    )
    return selected, manifest
