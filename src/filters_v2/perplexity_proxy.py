from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import unigram_surprisal_scores


class PerplexityProxyFilter(BaseFilter):
    filter_type = "perplexity_proxy"
    proxy_used = True

    def filter(self, records: list[FilterInput]):
        scores = unigram_surprisal_scores([record.text for record in records])
        decisions = [
            FilterDecision(
                doc_id=record.doc_id,
                keep=True,
                score=score,
                reason="perplexity_proxy",
                metadata={
                    "component_scores": {"unigram_inverse_surprisal": score},
                    "proxy_note": "unigram proxy only, not neural LM perplexity",
                },
            )
            for record, score in zip(records, scores, strict=False)
        ]
        result = self._result(records, decisions)
        self._last_records = list(records)
        self._last_result = result
        return result

    def score(self, record: FilterInput) -> FilterDecision:
        raise NotImplementedError("perplexity_proxy fits a corpus-level unigram proxy")
