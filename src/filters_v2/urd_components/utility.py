from __future__ import annotations

import math
from collections import Counter
from typing import Any

from filters_v2.base import FilterInput
from filters_v2.heuristics import clamp01, tokens


def _entropy(items: list[str]) -> float:
    if not items:
        return 0.0
    counts = Counter(items)
    total = sum(counts.values())
    value = 0.0
    for count in counts.values():
        probability = count / max(1, total)
        value -= probability * math.log(probability)
    return value / max(1.0, math.log(max(2, len(counts))))


def score_utility(record: FilterInput, records: list[FilterInput]) -> dict[str, Any]:
    """Return transparent utility proxies, not true training utility."""
    doc_tokens = tokens(record.text)
    corpus_counts = Counter(token for item in records for token in tokens(item.text))
    length_values = [max(1, len(tokens(item.text))) for item in records]
    max_len = max(length_values or [1])
    length_score = clamp01(math.log1p(len(doc_tokens)) / max(1.0, math.log1p(max_len)))
    lexical_informativeness = clamp01(length_score * (0.5 + 0.5 * len(set(doc_tokens)) / max(1, len(doc_tokens))))
    rare_hits = sum(1 for token in set(doc_tokens) if corpus_counts.get(token, 0) <= 1)
    rare_coverage = clamp01(rare_hits / max(1, len(set(doc_tokens))))
    entropy_score = clamp01(_entropy(doc_tokens))
    validation_similarity_proxy = clamp01(len(set(doc_tokens)) / max(1, len(set(corpus_counts))))
    utility_score = clamp01(
        0.35 * lexical_informativeness
        + 0.25 * rare_coverage
        + 0.25 * entropy_score
        + 0.15 * validation_similarity_proxy
    )
    return {
        "utility_score": utility_score,
        "utility_components": {
            "length_normalized_lexical_informativeness": lexical_informativeness,
            "rare_token_coverage_proxy": rare_coverage,
            "token_entropy_proxy": entropy_score,
            "validation_similarity_proxy": validation_similarity_proxy,
            "proxy_lm_available": False,
        },
        "utility_proxy_used": True,
        "utility_notes": "Lightweight proxy only; not measured training loss reduction.",
    }
