from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import clamp01, language_text_ratio, symbol_ratio, tokens, unique_word_ratio


class ClassifierQualityProxyFilter(BaseFilter):
    filter_type = "classifier_quality_proxy"
    proxy_used = True

    def score(self, record: FilterInput) -> FilterDecision:
        length_feature = min(1.0, len(tokens(record.text)) / 12)
        lexical_feature = unique_word_ratio(record.text)
        language_feature = language_text_ratio(record.text)
        symbol_feature = 1.0 - symbol_ratio(record.text)
        score = clamp01(
            0.30 * length_feature
            + 0.25 * lexical_feature
            + 0.25 * language_feature
            + 0.20 * symbol_feature
        )
        return FilterDecision(
            doc_id=record.doc_id,
            keep=score >= 0.20,
            score=score,
            reason="classifier_quality_proxy",
            metadata={
                "component_scores": {
                    "length_feature": length_feature,
                    "lexical_feature": lexical_feature,
                    "language_feature": language_feature,
                    "symbol_feature": symbol_feature,
                },
                "trained_classifier_artifact": "",
                "proxy_note": "deterministic proxy only, not a learned classifier baseline",
            },
        )
