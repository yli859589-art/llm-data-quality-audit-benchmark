from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import clamp01, language_text_ratio, symbol_ratio, unique_word_ratio


class CCNetStyleProxyFilter(BaseFilter):
    filter_type = "ccnet_style_proxy"
    proxy_used = True
    external_dependency = "fastText_language_id_or_CCNet_pipeline"
    external_dependency_available = False

    def score(self, record: FilterInput) -> FilterDecision:
        language_confidence_proxy = language_text_ratio(record.text)
        quality_proxy = unique_word_ratio(record.text)
        noise_penalty = symbol_ratio(record.text)
        score = clamp01(0.50 * language_confidence_proxy + 0.35 * quality_proxy + 0.15 * (1.0 - noise_penalty))
        return FilterDecision(
            doc_id=record.doc_id,
            keep=score >= 0.25,
            score=score,
            reason="ccnet_style_proxy",
            metadata={
                "component_scores": {
                    "language_confidence_proxy": language_confidence_proxy,
                    "quality_proxy": quality_proxy,
                    "symbol_noise_inverse": 1.0 - noise_penalty,
                },
                "external_dependency_available": False,
                "proxy_note": "protocol/proxy only; full CCNet baseline is not reproduced",
            },
        )
