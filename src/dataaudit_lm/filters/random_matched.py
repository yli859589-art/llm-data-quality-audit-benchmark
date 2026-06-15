from __future__ import annotations

from itertools import combinations

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.filters.base import FilterDecision, FilterResult, build_filter_manifest
from dataaudit_lm.integrity.hashing import stable_hash_int


def _best_small_subset(records: list[DataRecord], target_tokens: int) -> set[str]:
    best: tuple[int, tuple[str, ...]] | None = None
    ordered = sorted(records, key=lambda item: item.record_id)
    for size in range(1, min(len(ordered), 18) + 1):
        for subset in combinations(ordered, size):
            tokens = sum(record.token_count for record in subset)
            diff = abs(tokens - target_tokens)
            ids = tuple(record.record_id for record in subset)
            candidate = (diff, ids)
            if best is None or candidate < best:
                best = candidate
    return set(best[1]) if best else set()


def apply_random_token_matched(
    records: list[DataRecord],
    *,
    target_tokens: int,
    seed: int,
    target_name: str,
    tolerance: float = 0.01,
) -> FilterResult:
    if target_tokens <= 0:
        raise ValueError("target_tokens must be positive")
    ordered = sorted(records, key=lambda item: item.record_id)
    if len(ordered) <= 18:
        kept_ids = _best_small_subset(ordered, target_tokens)
    else:
        ranked = sorted(
            ordered,
            key=lambda record: (
                stable_hash_int(f"{seed}:{target_name}:{record.record_id}"),
                record.record_id,
            ),
        )
        kept_ids = set()
        total = 0
        for record in ranked:
            if total + record.token_count <= target_tokens or not kept_ids:
                kept_ids.add(record.record_id)
                total += record.token_count
            if total >= target_tokens:
                break
    kept = [record for record in ordered if record.record_id in kept_ids]
    selected_tokens = sum(record.token_count for record in kept)
    relative_error = abs(selected_tokens - target_tokens) / target_tokens
    decisions = [
        FilterDecision(
            record_id=record.record_id,
            kept=record.record_id in kept_ids,
            reason=(
                "random_token_matched_selected"
                if record.record_id in kept_ids
                else "random_token_matched_not_selected"
            ),
            metadata={"target_method": target_name},
        )
        for record in ordered
    ]
    manifest = build_filter_manifest(
        method_name=f"random_matched__{target_name}",
        records=records,
        decisions=decisions,
        parameters={
            "matching_policy": "selected_token_count",
            "seed": seed,
            "target_method": target_name,
            "target_tokens": target_tokens,
            "tolerance": tolerance,
        },
        notes="Random matched is a control; include as training method only when protocol freezes it.",
    )
    manifest["selected_tokens"] = selected_tokens
    manifest["token_match_relative_error"] = relative_error
    manifest["within_tolerance"] = relative_error <= tolerance
    return FilterResult(f"random_matched__{target_name}", len(records), kept, decisions, manifest)
