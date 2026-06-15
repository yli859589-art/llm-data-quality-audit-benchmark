from __future__ import annotations

import re

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.filters.base import FilterDecision, FilterResult, build_filter_manifest


def c4_quality_score(text: str) -> float:
    tokens = text.split()
    if not tokens:
        return 0.0
    alpha_chars = sum(char.isalpha() for char in text)
    digit_chars = sum(char.isdigit() for char in text)
    url_penalty = 0.2 if re.search(r"https?://|www\.", text) else 0.0
    markup_penalty = 0.2 if re.search(r"<[^>]+>", text) else 0.0
    alpha_ratio = alpha_chars / max(1, len(text))
    digit_penalty = min(0.3, digit_chars / max(1, len(text)))
    return max(0.0, min(1.0, alpha_ratio - digit_penalty - url_penalty - markup_penalty))


def apply_c4_quality_filter(records: list[DataRecord], *, min_score: float = 0.35) -> FilterResult:
    ordered = sorted(records, key=lambda item: item.record_id)
    kept: list[DataRecord] = []
    decisions: list[FilterDecision] = []
    for record in ordered:
        score = c4_quality_score(record.text)
        is_kept = score >= min_score
        if is_kept:
            kept.append(record)
        decisions.append(
            FilterDecision(
                record_id=record.record_id,
                kept=is_kept,
                reason="quality_score_passed" if is_kept else "quality_score_failed",
                score=score,
            )
        )
    manifest = build_filter_manifest(
        method_name="c4_inspired_quality_filter",
        records=records,
        decisions=decisions,
        parameters={"min_score": min_score, "rules": "alpha_digit_url_markup"},
    )
    return FilterResult("c4_inspired_quality_filter", len(records), kept, decisions, manifest)
