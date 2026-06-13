from __future__ import annotations

from typing import Any

from filters_v2.base import FilterInput
from filters_v2.heuristics import clamp01, tokens


def score_cost(record: FilterInput, records: list[FilterInput]) -> dict[str, Any]:
    token_counts = [max(1, len(tokens(item.text))) for item in records]
    max_tokens = max(token_counts or [1])
    doc_tokens = len(tokens(record.text))
    length_cost = clamp01(len(record.text) / max(1, max(len(item.text) for item in records)))
    token_cost = clamp01(doc_tokens / max(1, max_tokens))
    components = {
        "document_length_cost": length_cost,
        "estimated_token_cost": token_cost,
        "runtime_cost_proxy": token_cost,
        "dependency_cost": 0.0,
        "memory_cpu_proxy": token_cost,
        "flops_estimate": "unavailable",
    }
    numeric = [value for value in components.values() if isinstance(value, (int, float))]
    cost_score = clamp01(sum(float(value) for value in numeric) / max(1, len(numeric)))
    return {
        "cost_score": cost_score,
        "cost_components": components,
        "cost_proxy_used": True,
        "cost_notes": "Length/token/runtime proxy only; real FLOPs are not measured.",
    }
