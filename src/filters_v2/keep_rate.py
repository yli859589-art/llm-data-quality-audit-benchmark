from __future__ import annotations

import math
from typing import Sequence


def compute_document_keep_rate(input_docs: int, kept_docs: int) -> float:
    return kept_docs / max(1, input_docs)


def compute_token_keep_rate(input_tokens: int, kept_tokens: int) -> float:
    return kept_tokens / max(1, input_tokens)


def keep_count_for_rate(total: int, target_keep_rate: float | None) -> int:
    if target_keep_rate is None:
        return total
    if not 0 < target_keep_rate <= 1:
        raise ValueError("target_keep_rate must be in (0, 1]")
    return max(1, min(total, math.ceil(total * target_keep_rate)))


def select_top_k_by_keep_rate(
    records: Sequence[object],
    scores: Sequence[float],
    target_keep_rate: float | None,
) -> set[int]:
    if len(records) != len(scores):
        raise ValueError("records and scores must have the same length")
    keep_count = keep_count_for_rate(len(records), target_keep_rate)
    ranked = sorted(enumerate(scores), key=lambda item: (-item[1], item[0]))
    return {index for index, _ in ranked[:keep_count]}


def validate_keep_rate(actual: float, target: float | None, tolerance: float = 0.25) -> dict[str, object]:
    if target is None:
        return {"status": "not_applicable", "reason": "no target_keep_rate supplied"}
    difference = abs(actual - target)
    return {
        "status": "passed" if difference <= tolerance else "warning",
        "actual": actual,
        "target": target,
        "difference": difference,
        "tolerance": tolerance,
        "reason": "integer document counts may prevent exact keep-rate matching",
    }


def normalize_target_keep_rate(method_result: dict[str, object], reference_keep_rate: float) -> dict[str, object]:
    normalized = dict(method_result)
    normalized["reference_keep_rate"] = reference_keep_rate
    normalized["document_keep_rate_delta_vs_reference"] = float(
        normalized.get("document_keep_rate", 0.0)
    ) - reference_keep_rate
    return normalized
