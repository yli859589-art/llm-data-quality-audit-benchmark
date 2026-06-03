from __future__ import annotations

import math

from .quality import EMAIL_RE, ID_RE, PHONE_RE


def pii_hit_count(documents: list[str]) -> int:
    return sum(
        len(EMAIL_RE.findall(document))
        + len(PHONE_RE.findall(document))
        + len(ID_RE.findall(document))
        for document in documents
    )


def evaluate_synthetic_canaries(
    raw_documents: list[str],
    processed_documents: list[str],
    canaries: list[dict[str, str]],
) -> dict[str, object]:
    raw = "\n".join(raw_documents)
    processed = "\n".join(processed_documents)
    values = [value for canary in canaries for value in canary.values()]
    detected_before = sum(value in raw for value in values)
    residual_after = sum(value in processed for value in values)
    removed = detected_before - residual_after
    placeholders = sum(processed.count(marker) for marker in ("<EMAIL>", "<PHONE>", "<ID>"))
    side_effects = max(0, placeholders - removed)
    false_positive_rate = side_effects / max(1, placeholders)
    return {
        "synthetic_canary_values": len(values),
        "detected_before_processing": detected_before,
        "residual_canary_values_after_processing": residual_after,
        "synthetic_canary_removal_recall": removed / max(1, detected_before),
        "synthetic_canary_removal_precision": removed / max(1, removed + side_effects),
        "synthetic_canary_false_positive_rate": false_positive_rate,
        "redaction_placeholders": placeholders,
        "redaction_validation_side_effect_count": side_effects,
        "lightweight_exposure_reduction_bits": math.log2(
            (detected_before + 1) / (residual_after + 1)
        ),
        "canary_memorization_status": (
            "no_residual_synthetic_canary_values"
            if residual_after == 0
            else "residual_synthetic_canary_values_detected"
        ),
        "note": (
            "This is a synthetic-canary redaction validation, not a formal "
            "membership-inference or memorization study."
        ),
    }
