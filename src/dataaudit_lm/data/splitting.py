from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.integrity.hashing import sha256_json, stable_hash_int

SplitName = Literal["train", "valid", "test"]


@dataclass(frozen=True)
class SplitManifest:
    split_algorithm: str
    ratios: dict[str, float]
    seed: int
    split_counts: dict[str, int]
    split_tokens: dict[str, int]
    cluster_count: int
    cluster_cross_split_violations: int
    manifest_hash: str


def _validate_ratios(ratios: dict[str, float]) -> None:
    if set(ratios) != {"train", "valid", "test"}:
        raise ValueError("ratios must contain train, valid, and test")
    total = sum(ratios.values())
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"split ratios must sum to 1.0, got {total}")
    if any(value < 0 for value in ratios.values()):
        raise ValueError("split ratios must be non-negative")


def cluster_aware_hash_split(
    records: list[DataRecord],
    *,
    ratios: dict[str, float] | None = None,
    seed: int = 0,
) -> tuple[dict[str, list[DataRecord]], SplitManifest]:
    """Assign exact-duplicate clusters to deterministic splits without splitting a cluster."""
    ratios = ratios or {"train": 0.95, "valid": 0.025, "test": 0.025}
    _validate_ratios(ratios)

    clusters: dict[str, list[DataRecord]] = defaultdict(list)
    for record in records:
        clusters[record.content_sha256].append(record)

    splits: dict[str, list[DataRecord]] = {"train": [], "valid": [], "test": []}
    train_cut = ratios["train"]
    valid_cut = ratios["train"] + ratios["valid"]

    for cluster_key, members in sorted(clusters.items()):
        value = stable_hash_int(f"{seed}:{cluster_key}") / float(16**16)
        split: SplitName
        if value < train_cut:
            split = "train"
        elif value < valid_cut:
            split = "valid"
        else:
            split = "test"
        splits[split].extend(sorted(members, key=lambda item: item.record_id))

    split_counts = {name: len(items) for name, items in splits.items()}
    split_tokens = {name: sum(item.token_count for item in items) for name, items in splits.items()}
    payload = {
        "algorithm": "cluster_aware_deterministic_hash_split_v1",
        "clusters": sorted(clusters),
        "ratios": ratios,
        "seed": seed,
        "split_counts": split_counts,
        "split_tokens": split_tokens,
    }
    manifest = SplitManifest(
        split_algorithm="cluster_aware_deterministic_hash_split_v1",
        ratios=dict(ratios),
        seed=seed,
        split_counts=split_counts,
        split_tokens=split_tokens,
        cluster_count=len(clusters),
        cluster_cross_split_violations=0,
        manifest_hash=sha256_json(payload),
    )
    return splits, manifest
