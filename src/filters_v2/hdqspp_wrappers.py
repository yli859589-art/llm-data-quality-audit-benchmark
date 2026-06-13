from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import clamp01, language_text_ratio, symbol_ratio, unique_word_ratio


class HDQSppHistoricalFilter(BaseFilter):
    filter_type = "hdqspp_historical"
    historical_baseline = True

    def score(self, record: FilterInput) -> FilterDecision:
        lexical = unique_word_ratio(record.text)
        language = language_text_ratio(record.text)
        symbol = 1.0 - symbol_ratio(record.text)
        score = clamp01(0.45 * lexical + 0.35 * language + 0.20 * symbol)
        return FilterDecision(
            doc_id=record.doc_id,
            keep=True,
            score=score,
            reason="hdqspp_historical_scored_keep",
            metadata={
                "component_scores": {
                    "lexical_proxy": lexical,
                    "language_proxy": language,
                    "symbol_proxy": symbol,
                },
                "historical_baseline": True,
                "failure_analysis_object": True,
                "claim_boundary": "historical wrapper only; not method-success evidence",
            },
        )
