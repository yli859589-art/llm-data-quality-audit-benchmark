from __future__ import annotations

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.data.sampling import SampleManifest, corpus_wide_token_sample


def build_training_sample(
    records: list[DataRecord],
    *,
    token_budget: int,
    seed: int,
) -> tuple[list[DataRecord], SampleManifest]:
    return corpus_wide_token_sample(records, token_budget=token_budget, seed=seed)
