from __future__ import annotations

from .base import BaseFilter, FilterDecision, FilterInput


class RawFilter(BaseFilter):
    filter_type = "raw"

    def score(self, record: FilterInput) -> FilterDecision:
        return FilterDecision(
            doc_id=record.doc_id,
            keep=True,
            score=1.0,
            reason="raw_keep_all",
            metadata={"component_scores": {"raw": 1.0}},
        )
