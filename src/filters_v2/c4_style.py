from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import HTML_RE, URL_RE, clamp01, language_text_ratio, punctuation_ratio, repeated_line_ratio, symbol_ratio, tokens


class C4StyleProxyFilter(BaseFilter):
    filter_type = "c4_style_proxy"
    proxy_used = True

    def score(self, record: FilterInput) -> FilterDecision:
        word_count = len(tokens(record.text))
        min_word_score = min(1.0, word_count / 5)
        symbol_score = 1.0 - min(1.0, 4 * symbol_ratio(record.text))
        punctuation_score = 1.0 - min(1.0, 3 * punctuation_ratio(record.text))
        noise_score = 1.0 - min(1.0, 0.4 * (len(URL_RE.findall(record.text)) + len(HTML_RE.findall(record.text))))
        repeated_score = 1.0 - repeated_line_ratio(record.text)
        language_score = language_text_ratio(record.text)
        score = clamp01(
            0.20 * min_word_score
            + 0.20 * symbol_score
            + 0.15 * punctuation_score
            + 0.15 * noise_score
            + 0.15 * repeated_score
            + 0.15 * language_score
        )
        return FilterDecision(
            doc_id=record.doc_id,
            keep=score >= 0.25,
            score=score,
            reason="c4_style_proxy",
            metadata={
                "component_scores": {
                    "min_word_score": min_word_score,
                    "symbol_score": symbol_score,
                    "punctuation_score": punctuation_score,
                    "url_html_noise_score": noise_score,
                    "repeated_line_score": repeated_score,
                    "language_text_score": language_score,
                },
                "proxy_note": "transparent C4-style heuristic proxy, not official C4 reproduction",
            },
        )
