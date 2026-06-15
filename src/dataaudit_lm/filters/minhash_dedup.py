from __future__ import annotations

import re
from collections import defaultdict

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.filters.base import FilterDecision, FilterResult, build_filter_manifest


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", text.lower())).strip()


def word_shingles(text: str, *, ngram_size: int = 5) -> set[tuple[str, ...]]:
    tokens = normalize_text(text).split()
    if len(tokens) < ngram_size:
        return {tuple(tokens)} if tokens else set()
    return {
        tuple(tokens[index : index + ngram_size]) for index in range(len(tokens) - ngram_size + 1)
    }


def jaccard(left: set[tuple[str, ...]], right: set[tuple[str, ...]]) -> float:
    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


class _UnionFind:
    def __init__(self, ids: list[str]) -> None:
        self.parent = {item: item for item in ids}

    def find(self, item: str) -> str:
        parent = self.parent[item]
        if parent != item:
            self.parent[item] = self.find(parent)
        return self.parent[item]

    def union(self, left: str, right: str) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return
        winner, loser = sorted([left_root, right_root])
        self.parent[loser] = winner


def apply_minhash_near_dedup(
    records: list[DataRecord],
    *,
    threshold: float = 0.8,
    ngram_size: int = 5,
    num_perm: int = 64,
) -> FilterResult:
    """Deterministic near-dedup rehearsal implementation using exact Jaccard on shingles."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be in [0, 1]")
    ordered = sorted(records, key=lambda item: item.record_id)
    shingle_map = {
        record.record_id: word_shingles(record.text, ngram_size=ngram_size) for record in ordered
    }
    uf = _UnionFind([record.record_id for record in ordered])
    pair_scores: list[dict[str, object]] = []
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            score = jaccard(shingle_map[left.record_id], shingle_map[right.record_id])
            if score >= threshold:
                uf.union(left.record_id, right.record_id)
                pair_scores.append(
                    {"left": left.record_id, "right": right.record_id, "jaccard_estimate": score}
                )

    clusters: dict[str, list[DataRecord]] = defaultdict(list)
    for record in ordered:
        clusters[uf.find(record.record_id)].append(record)

    kept_ids = {
        sorted(members, key=lambda item: item.record_id)[0].record_id
        for members in clusters.values()
    }
    kept = [record for record in ordered if record.record_id in kept_ids]
    decisions = [
        FilterDecision(
            record_id=record.record_id,
            kept=record.record_id in kept_ids,
            reason=(
                "near_dedup_representative" if record.record_id in kept_ids else "near_duplicate"
            ),
            metadata={"cluster_id": uf.find(record.record_id)},
        )
        for record in ordered
    ]
    cluster_manifest = [
        {
            "cluster_id": cluster_id,
            "cluster_size": len(members),
            "representative_id": sorted(members, key=lambda item: item.record_id)[0].record_id,
            "member_ids": [
                record.record_id for record in sorted(members, key=lambda item: item.record_id)
            ],
        }
        for cluster_id, members in sorted(clusters.items())
    ]
    manifest = build_filter_manifest(
        method_name="minhash_near_dedup",
        records=records,
        decisions=decisions,
        parameters={
            "normalization": "lowercase_alnum_whitespace",
            "ngram_type": "word",
            "ngram_size": ngram_size,
            "num_perm": num_perm,
            "lsh_threshold": threshold,
            "cluster_resolution": "union_find",
            "representative_rule": "lexicographically_smallest_record_id",
        },
    )
    manifest["clusters"] = cluster_manifest
    manifest["pair_scores"] = pair_scores
    return FilterResult("minhash_near_dedup", len(records), kept, decisions, manifest)
