from __future__ import annotations

from dataclasses import dataclass

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.filters.base import FilterDecision, FilterResult, build_filter_manifest
from dataaudit_lm.filters.quality_rules import c4_quality_score
from dataaudit_lm.filters.reference_lm import FrozenUnigramReferenceLM


@dataclass(frozen=True)
class SelectorWeights:
    quality: float = 0.35
    reference_nll: float = -0.35
    length_balance: float = 0.2
    duplicate_penalty: float = -0.1


def _length_balance(record: DataRecord, target_tokens: int) -> float:
    return 1.0 / (1.0 + abs(record.token_count - target_tokens))


def apply_dataaudit_selector(
    records: list[DataRecord],
    *,
    reference_lm: FrozenUnigramReferenceLM,
    weights: SelectorWeights | None = None,
    keep_fraction: float = 0.5,
    target_tokens: int = 128,
) -> FilterResult:
    if not 0.0 < keep_fraction <= 1.0:
        raise ValueError("keep_fraction must be in (0, 1]")
    weights = weights or SelectorWeights()
    ordered = sorted(records, key=lambda item: item.record_id)
    content_counts: dict[str, int] = {}
    for record in ordered:
        content_counts[record.content_sha256] = content_counts.get(record.content_sha256, 0) + 1
    scores: dict[str, float] = {}
    for record in ordered:
        reference_score = reference_lm.score(record).reference_nll
        duplicate_penalty = 1.0 if content_counts[record.content_sha256] > 1 else 0.0
        scores[record.record_id] = (
            weights.quality * c4_quality_score(record.text)
            + weights.reference_nll * reference_score
            + weights.length_balance * _length_balance(record, target_tokens)
            + weights.duplicate_penalty * duplicate_penalty
        )
    keep_count = max(1, round(len(ordered) * keep_fraction))
    kept_ids = {
        record_id
        for record_id, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[
            :keep_count
        ]
    }
    kept = [record for record in ordered if record.record_id in kept_ids]
    decisions = [
        FilterDecision(
            record_id=record.record_id,
            kept=record.record_id in kept_ids,
            reason="selector_selected" if record.record_id in kept_ids else "selector_rejected",
            score=scores[record.record_id],
            metadata={"selector_version": "dataaudit_selector_rehearsal_v1"},
        )
        for record in ordered
    ]
    manifest = build_filter_manifest(
        method_name="dataaudit_selector",
        records=records,
        decisions=decisions,
        parameters={
            "keep_fraction": keep_fraction,
            "target_tokens": target_tokens,
            "weights": weights.__dict__,
            "weight_freeze_policy": "development_subset_only_not_test_tuned",
        },
        notes="Selector hypothesis is documented separately; single-seed rehearsal is engineering validation only.",
    )
    return FilterResult("dataaudit_selector", len(records), kept, decisions, manifest)


def pareto_selected_ids(
    records: list[DataRecord], score_columns: dict[str, dict[str, float]]
) -> set[str]:
    ids = [record.record_id for record in records]
    selected: set[str] = set()
    for candidate in ids:
        dominated = False
        for challenger in ids:
            if challenger == candidate:
                continue
            better_or_equal = all(
                score_columns[column][challenger] >= score_columns[column][candidate]
                for column in score_columns
            )
            strictly_better = any(
                score_columns[column][challenger] > score_columns[column][candidate]
                for column in score_columns
            )
            if better_or_equal and strictly_better:
                dominated = True
                break
        if not dominated:
            selected.add(candidate)
    return selected
