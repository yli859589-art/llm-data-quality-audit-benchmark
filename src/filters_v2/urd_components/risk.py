from __future__ import annotations

from collections import Counter
from typing import Any

from filters_v2.base import FilterInput
from filters_v2.heuristics import HTML_RE, URL_RE, clamp01, repeated_line_ratio, symbol_ratio, tokens
from filters_v2.risk import EMAIL_RE, PHONE_RE


def _ratio(value: float, total: float) -> float:
    return value / max(1.0, total)


def score_risk(record: FilterInput, records: list[FilterInput]) -> dict[str, Any]:
    text = record.text
    chars = max(1, len(text))
    normalized_counts = Counter(" ".join(item.text.casefold().split()) for item in records)
    duplicate_hint = 1.0 if normalized_counts[" ".join(text.casefold().split())] > 1 else 0.0
    boilerplate_terms = ["copyright", "subscribe", "cookie", "terms of use", "privacy policy"]
    boilerplate_hint = 1.0 if any(term in text.casefold() for term in boilerplate_terms) else 0.0
    components = {
        "url_ratio": clamp01(len(URL_RE.findall(text)) / max(1, len(tokens(text)))),
        "html_noise_ratio": clamp01(len(HTML_RE.findall(text)) / max(1, len(tokens(text)))),
        "symbol_ratio": clamp01(symbol_ratio(text) * 3.0),
        "repetition_ratio": clamp01(repeated_line_ratio(text)),
        "digit_ratio": clamp01(_ratio(sum(char.isdigit() for char in text), chars) * 3.0),
        "estimated_pii_pattern_hits": clamp01((len(EMAIL_RE.findall(text)) + len(PHONE_RE.findall(text))) / 2.0),
        "boilerplate_hint": boilerplate_hint,
        "duplicate_hint": duplicate_hint,
        "toxicity_classifier": "unavailable",
    }
    numeric = [value for value in components.values() if isinstance(value, (int, float))]
    risk_score = clamp01(sum(float(value) for value in numeric) / max(1, len(numeric)))
    return {
        "risk_score": risk_score,
        "risk_components": components,
        "risk_proxy_used": True,
        "risk_notes": "Heuristic risk proxy; no safety classifier or toxicity model is used.",
    }
