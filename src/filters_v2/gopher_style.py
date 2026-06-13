from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import clamp01, language_text_ratio, repeated_line_ratio, stopword_ratio, symbol_ratio, tokens, unique_word_ratio


class GopherStyleProxyFilter(BaseFilter):
    filter_type = "gopher_style_proxy"
    proxy_used = True

    def score(self, record: FilterInput) -> FilterDecision:
        length_score = min(1.0, len(tokens(record.text)) / 8)
        repetition_score = 1.0 - repeated_line_ratio(record.text)
        stopword_score = min(1.0, 3.0 * stopword_ratio(record.text))
        symbol_score = 1.0 - min(1.0, 4 * symbol_ratio(record.text))
        unique_score = unique_word_ratio(record.text)
        language_score = language_text_ratio(record.text)
        score = clamp01(
            0.20 * length_score
            + 0.20 * repetition_score
            + 0.15 * stopword_score
            + 0.15 * symbol_score
            + 0.15 * unique_score
            + 0.15 * language_score
        )
        return FilterDecision(
            doc_id=record.doc_id,
            keep=score >= 0.25,
            score=score,
            reason="gopher_style_proxy",
            metadata={
                "component_scores": {
                    "length_score": length_score,
                    "repetition_score": repetition_score,
                    "stopword_score": stopword_score,
                    "symbol_score": symbol_score,
                    "unique_word_score": unique_score,
                    "language_score": language_score,
                },
                "proxy_note": "transparent Gopher-style heuristic proxy, not official Gopher reproduction",
            },
        )
