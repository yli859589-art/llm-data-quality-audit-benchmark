from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from filters_v2.base import FilterInput
from filters_v2.heuristics import clamp01, jaccard, token_set, tokens


def score_shift(record: FilterInput, records: list[FilterInput]) -> dict[str, Any]:
    doc_tokens = tokens(record.text)
    lengths = [len(tokens(item.text)) for item in records]
    mean_length = mean(lengths) if lengths else 0.0
    max_length = max(lengths or [1])
    length_shift = abs(len(doc_tokens) - mean_length) / max(1.0, max_length)
    corpus_tokens = set(token for item in records for token in tokens(item.text))
    token_shift = 1.0 - jaccard(token_set(record.text), corpus_tokens)
    source_counts = Counter(item.source for item in records if item.source)
    if record.source and source_counts:
        source_shift = 1.0 - source_counts[record.source] / max(1, sum(source_counts.values()))
    else:
        source_shift = 0.0
    components = {
        "length_distribution_shift_proxy": clamp01(length_shift),
        "vocabulary_distribution_shift_proxy": clamp01(token_shift),
        "source_domain_distribution_shift_proxy": clamp01(source_shift),
        "reference_corpus_statistics": "input_relative_proxy",
    }
    shift_penalty = clamp01(
        0.40 * components["length_distribution_shift_proxy"]
        + 0.40 * components["vocabulary_distribution_shift_proxy"]
        + 0.20 * components["source_domain_distribution_shift_proxy"]
    )
    return {
        "shift_penalty": shift_penalty,
        "shift_components": components,
        "shift_proxy_used": True,
        "shift_notes": "Input-relative shift proxy only; Step 8 is reserved for mechanism analysis.",
    }
