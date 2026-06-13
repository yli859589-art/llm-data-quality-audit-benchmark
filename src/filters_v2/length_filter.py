from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput


class LengthFilter(BaseFilter):
    filter_type = "length_filter"

    def score(self, record: FilterInput) -> FilterDecision:
        min_tokens = int(self.config.params.get("min_estimated_tokens", 1))
        max_tokens = int(self.config.params.get("max_estimated_tokens", 1000000000))
        length = record.estimated_tokens
        keep = min_tokens <= length <= max_tokens
        if keep:
            reason = "length_in_range"
            score = 1.0
        elif length < min_tokens:
            reason = "length_below_min"
            score = 0.0
        else:
            reason = "length_above_max"
            score = 0.0
        return FilterDecision(
            doc_id=record.doc_id,
            keep=keep,
            score=score,
            reason=reason,
            metadata={
                "component_scores": {"estimated_tokens": length},
                "min_estimated_tokens": min_tokens,
                "max_estimated_tokens": max_tokens,
            },
        )
