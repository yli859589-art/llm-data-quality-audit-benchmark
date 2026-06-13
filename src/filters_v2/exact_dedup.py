from __future__ import annotations

import hashlib

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import normalize_text


class ExactDedupFilter(BaseFilter):
    filter_type = "exact_dedup"

    def filter(self, records: list[FilterInput]):
        seen: set[str] = set()
        decisions: list[FilterDecision] = []
        for record in records:
            normalized = normalize_text(record.text)
            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
            keep = digest not in seen
            seen.add(digest)
            decisions.append(
                FilterDecision(
                    doc_id=record.doc_id,
                    keep=keep,
                    score=1.0 if keep else 0.0,
                    reason="unique_kept" if keep else "exact_duplicate_removed",
                    metadata={"component_scores": {"exact_dedup": 1.0 if keep else 0.0}, "text_hash": digest},
                )
            )
        result = self._result(records, decisions)
        self._last_records = list(records)
        self._last_result = result
        return result

    def score(self, record: FilterInput) -> FilterDecision:
        raise NotImplementedError("exact_dedup uses batch-level duplicate tracking")
