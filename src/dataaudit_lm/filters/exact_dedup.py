from __future__ import annotations

from collections import defaultdict

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.filters.base import FilterDecision, FilterResult, build_filter_manifest


def apply_exact_dedup(records: list[DataRecord]) -> FilterResult:
    clusters: dict[str, list[DataRecord]] = defaultdict(list)
    for record in records:
        clusters[record.content_sha256].append(record)

    representatives: dict[str, str] = {}
    cluster_manifest: list[dict[str, object]] = []
    duplicate_count = 0
    token_reduction = 0
    for cluster_key, members in sorted(clusters.items()):
        ordered = sorted(members, key=lambda item: item.record_id)
        representatives[cluster_key] = ordered[0].record_id
        cluster_duplicate_count = max(0, len(ordered) - 1)
        cluster_token_reduction = sum(record.token_count for record in ordered[1:])
        duplicate_count += cluster_duplicate_count
        token_reduction += cluster_token_reduction
        cluster_manifest.append(
            {
                "cluster_id": cluster_key,
                "cluster_size": len(ordered),
                "representative_id": ordered[0].record_id,
                "member_ids": [record.record_id for record in ordered],
                "duplicate_count": cluster_duplicate_count,
                "token_reduction": cluster_token_reduction,
            }
        )

    decisions: list[FilterDecision] = []
    kept: list[DataRecord] = []
    for record in sorted(records, key=lambda item: item.record_id):
        representative = representatives[record.content_sha256]
        is_kept = record.record_id == representative
        if is_kept:
            kept.append(record)
        decisions.append(
            FilterDecision(
                record_id=record.record_id,
                kept=is_kept,
                reason="exact_cluster_representative" if is_kept else "exact_duplicate",
                metadata={"cluster_id": record.content_sha256, "representative_id": representative},
            )
        )

    manifest = build_filter_manifest(
        method_name="exact_dedup",
        records=records,
        decisions=decisions,
        parameters={"representative_rule": "lexicographically_smallest_record_id"},
        notes="NULL_EFFECT_CONTROL if duplicate_count is zero.",
    )
    manifest["clusters"] = cluster_manifest
    manifest["duplicate_count"] = duplicate_count
    manifest["token_reduction"] = token_reduction
    manifest["method_role"] = (
        "NULL_EFFECT_CONTROL" if manifest["duplicate_count"] == 0 else "INDEPENDENT_FILTER"
    )
    return FilterResult("exact_dedup", len(records), kept, decisions, manifest)
