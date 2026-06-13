from __future__ import annotations

import random
import time

from .base import BaseFilter, FilterDecision, FilterInput
from .keep_rate import keep_count_for_rate


class RandomSameKeepRateFilter(BaseFilter):
    filter_type = "random_same_keep_rate"

    def score(self, record: FilterInput) -> FilterDecision:
        raise NotImplementedError("random_same_keep_rate uses batch-level seeded selection")

    def filter(self, records: list[FilterInput]):
        started = time.perf_counter()
        indexed = list(enumerate(records))
        rng = random.Random(self.config.seed)
        rng.shuffle(indexed)
        keep_count = keep_count_for_rate(len(records), self.config.target_keep_rate)
        kept_indices = {index for index, _ in indexed[:keep_count]}
        decisions = []
        for index, record in enumerate(records):
            keep = index in kept_indices
            decisions.append(
                FilterDecision(
                    doc_id=record.doc_id,
                    keep=keep,
                    score=1.0 if keep else 0.0,
                    reason="random_same_keep_rate",
                    metadata={
                        "component_scores": {"seeded_random_keep": 1.0 if keep else 0.0},
                        "seed": self.config.seed,
                    },
                )
            )
        result = self._result(records, decisions)
        self._last_records = list(records)
        self._last_result = result
        self._last_runtime_seconds = time.perf_counter() - started
        return result
