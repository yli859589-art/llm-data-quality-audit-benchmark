from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import jaccard, token_set


class MinHashNearDedupProxyFilter(BaseFilter):
    filter_type = "minhash_near_dedup_proxy"
    proxy_used = True

    def filter(self, records: list[FilterInput]):
        threshold = float(self.config.params.get("similarity_threshold", 0.86))
        seen_sets: list[set[str]] = []
        decisions: list[FilterDecision] = []
        for record in records:
            current = token_set(record.text)
            max_similarity = max((jaccard(current, prior) for prior in seen_sets), default=0.0)
            keep = max_similarity < threshold
            if keep:
                seen_sets.append(current)
            decisions.append(
                FilterDecision(
                    doc_id=record.doc_id,
                    keep=keep,
                    score=1.0 - max_similarity,
                    reason="near_duplicate_proxy" if not keep else "near_unique_proxy_kept",
                    metadata={
                        "component_scores": {"max_jaccard_similarity": max_similarity},
                        "proxy_note": "lightweight token-set Jaccard approximation, not full MinHash",
                    },
                )
            )
        result = self._result(records, decisions)
        self._last_records = list(records)
        self._last_result = result
        return result

    def score(self, record: FilterInput) -> FilterDecision:
        raise NotImplementedError("near dedup proxy uses batch-level comparisons")
