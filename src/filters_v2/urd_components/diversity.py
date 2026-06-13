from __future__ import annotations

import math
from collections import Counter
from typing import Any

from filters_v2.base import FilterInput
from filters_v2.heuristics import clamp01, jaccard, token_set, tokens


def _entropy(items: list[str]) -> float:
    if not items:
        return 0.0
    counts = Counter(items)
    total = sum(counts.values())
    entropy = 0.0
    for count in counts.values():
        probability = count / max(1, total)
        entropy -= probability * math.log(probability)
    return entropy / max(1.0, math.log(max(2, len(counts))))


def score_diversity(record: FilterInput, records: list[FilterInput]) -> dict[str, Any]:
    doc_tokens = tokens(record.text)
    doc_set = set(doc_tokens)
    all_sets = [token_set(item.text) for item in records if item.doc_id != record.doc_id]
    novelty = 1.0
    if all_sets:
        novelty = 1.0 - sum(jaccard(doc_set, item) for item in all_sets) / len(all_sets)
    source_values = {item.source for item in records if item.source}
    source_coverage = 1.0 / max(1, len(source_values)) if record.source else 0.0
    components = {
        "lexical_diversity": clamp01(len(doc_set) / max(1, len(doc_tokens))),
        "unique_token_ratio": clamp01(len(doc_set) / max(1, len(doc_tokens))),
        "character_word_entropy": clamp01((_entropy(list(record.text)) + _entropy(doc_tokens)) / 2.0),
        "source_domain_coverage_proxy": clamp01(source_coverage),
        "hash_vector_novelty_proxy": clamp01(novelty),
        "cluster_coverage_proxy": clamp01(novelty),
        "neural_embedding_diversity": "unavailable",
    }
    diversity_score = clamp01(
        0.25 * components["lexical_diversity"]
        + 0.20 * components["unique_token_ratio"]
        + 0.20 * components["character_word_entropy"]
        + 0.15 * components["source_domain_coverage_proxy"]
        + 0.20 * components["hash_vector_novelty_proxy"]
    )
    return {
        "diversity_score": diversity_score,
        "diversity_components": components,
        "diversity_proxy_used": True,
        "diversity_notes": "Hash/lexical diversity proxy; no neural embedding baseline is used.",
    }
