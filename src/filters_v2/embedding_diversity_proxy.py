from __future__ import annotations

import time

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import jaccard, token_set
from .keep_rate import keep_count_for_rate


class EmbeddingDiversityProxyFilter(BaseFilter):
    filter_type = "embedding_diversity_proxy"
    proxy_used = True

    def filter(self, records: list[FilterInput]):
        started = time.perf_counter()
        keep_count = keep_count_for_rate(len(records), self.config.target_keep_rate)
        sets = [token_set(record.text) for record in records]
        selected: list[int] = []
        if records:
            selected.append(0)
        while len(selected) < keep_count:
            candidates = [index for index in range(len(records)) if index not in selected]
            if not candidates:
                break
            best = max(
                candidates,
                key=lambda index: min(1.0 - jaccard(sets[index], sets[prior]) for prior in selected),
            )
            selected.append(best)
        selected_set = set(selected)
        decisions = []
        for index, record in enumerate(records):
            diversity_score = (
                min((1.0 - jaccard(sets[index], sets[prior]) for prior in selected_set if prior != index), default=1.0)
                if records
                else 0.0
            )
            decisions.append(
                FilterDecision(
                    doc_id=record.doc_id,
                    keep=index in selected_set,
                    score=diversity_score,
                    reason="embedding_diversity_proxy",
                    metadata={
                        "component_scores": {"token_set_diversity": diversity_score},
                        "proxy_note": "token-set diversity proxy, not neural embedding diversity",
                    },
                )
            )
        result = self._result(records, decisions)
        self._last_records = list(records)
        self._last_result = result
        self._last_runtime_seconds = time.perf_counter() - started
        return result

    def score(self, record: FilterInput) -> FilterDecision:
        raise NotImplementedError("embedding_diversity_proxy uses batch-level diverse selection")
