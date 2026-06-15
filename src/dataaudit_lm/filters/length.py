from __future__ import annotations

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.filters.base import FilterDecision, FilterResult, build_filter_manifest


def apply_length_filter(
    records: list[DataRecord],
    *,
    min_tokens: int,
    max_tokens: int,
) -> FilterResult:
    if min_tokens < 0 or max_tokens < min_tokens:
        raise ValueError("invalid token bounds")
    ordered = sorted(records, key=lambda item: item.record_id)
    decisions: list[FilterDecision] = []
    kept: list[DataRecord] = []
    for record in ordered:
        is_kept = min_tokens <= record.token_count <= max_tokens
        if is_kept:
            kept.append(record)
        decisions.append(
            FilterDecision(
                record_id=record.record_id,
                kept=is_kept,
                reason="within_length_bounds" if is_kept else "outside_length_bounds",
                score=float(record.token_count),
            )
        )
    manifest = build_filter_manifest(
        method_name="length_filter",
        records=records,
        decisions=decisions,
        parameters={"min_tokens": min_tokens, "max_tokens": max_tokens},
    )
    return FilterResult("length_filter", len(records), kept, decisions, manifest)
