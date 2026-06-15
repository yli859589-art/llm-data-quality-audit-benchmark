from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.filters.base import FilterDecision, FilterResult, build_filter_manifest
from dataaudit_lm.integrity.hashing import sha256_json


@dataclass(frozen=True)
class ReferenceScore:
    document_id: str
    reference_nll: float
    scored_tokens: int
    window_count: int
    score_status: str
    model_revision: str


class FrozenUnigramReferenceLM:
    """Small frozen reference LM for rehearsal; formal protocol can swap in a neural LM."""

    def __init__(self, reference_texts: list[str], *, alpha: float = 0.5) -> None:
        self.alpha = alpha
        tokens = [token for text in reference_texts for token in text.lower().split()]
        self.counts = Counter(tokens)
        self.total = sum(self.counts.values())
        self.vocab = sorted(set(tokens))
        self.model_revision = sha256_json(
            {"alpha": alpha, "counts": dict(sorted(self.counts.items()))}
        )

    def score(
        self, record: DataRecord, *, window_length: int = 128, stride: int = 128
    ) -> ReferenceScore:
        tokens = record.text.lower().split()
        if not tokens:
            return ReferenceScore(
                record.record_id, math.inf, 0, 0, "empty_document", self.model_revision
            )
        vocab_size = max(1, len(self.vocab))
        denominator = self.total + self.alpha * vocab_size
        nll = 0.0
        for token in tokens:
            probability = (self.counts.get(token, 0) + self.alpha) / denominator
            nll -= math.log(probability)
        window_count = max(1, math.ceil(max(1, len(tokens) - window_length) / max(1, stride)) + 1)
        return ReferenceScore(
            document_id=record.record_id,
            reference_nll=nll / len(tokens),
            scored_tokens=len(tokens),
            window_count=window_count,
            score_status="scored",
            model_revision=self.model_revision,
        )


def apply_reference_lm_filter(
    records: list[DataRecord],
    *,
    reference_lm: FrozenUnigramReferenceLM,
    keep_lowest_fraction: float = 0.5,
    window_length: int = 128,
    stride: int = 128,
) -> FilterResult:
    if not 0.0 < keep_lowest_fraction <= 1.0:
        raise ValueError("keep_lowest_fraction must be in (0, 1]")
    ordered = sorted(records, key=lambda item: item.record_id)
    scores = {
        record.record_id: reference_lm.score(record, window_length=window_length, stride=stride)
        for record in ordered
    }
    keep_count = max(1, round(len(ordered) * keep_lowest_fraction))
    kept_ids = {
        record_id
        for record_id, _score in sorted(
            scores.items(), key=lambda item: (item[1].reference_nll, item[0])
        )[:keep_count]
    }
    kept = [record for record in ordered if record.record_id in kept_ids]
    decisions = [
        FilterDecision(
            record_id=record.record_id,
            kept=record.record_id in kept_ids,
            reason=(
                "low_reference_lm_nll" if record.record_id in kept_ids else "high_reference_lm_nll"
            ),
            score=scores[record.record_id].reference_nll,
            metadata={
                "scored_tokens": scores[record.record_id].scored_tokens,
                "window_count": scores[record.record_id].window_count,
                "score_status": scores[record.record_id].score_status,
                "model_revision": scores[record.record_id].model_revision,
            },
        )
        for record in ordered
    ]
    manifest = build_filter_manifest(
        method_name="reference_lm_perplexity_filter",
        records=records,
        decisions=decisions,
        parameters={
            "reference_model": "FrozenUnigramReferenceLM",
            "model_revision": reference_lm.model_revision,
            "tokenizer_revision": "whitespace_rehearsal",
            "window_length": window_length,
            "stride": stride,
            "keep_lowest_fraction": keep_lowest_fraction,
            "device": "cpu",
            "score_cache_schema": "document_id/reference_nll/scored_tokens/window_count/status",
        },
        notes="Rehearsal reference LM scorer; not the old surface perplexity proxy.",
    )
    manifest["scores"] = [score.__dict__ for score in scores.values()]
    return FilterResult("reference_lm_perplexity_filter", len(records), kept, decisions, manifest)
