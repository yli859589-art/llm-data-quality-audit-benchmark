from __future__ import annotations

from dataaudit_lm.data.records import make_record
from dataaudit_lm.training.sampling import build_training_sample


def test_training_sampling_uses_full_corpus_not_input_prefix() -> None:
    records = [
        make_record(
            record_id=f"r{i}",
            source_row_id=str(i),
            text=f"text {i}",
            source_dataset="toy",
            source_revision="r",
            token_count=2,
        )
        for i in range(10)
    ]

    sample, manifest = build_training_sample(records, token_budget=8, seed=5)
    reversed_sample, reversed_manifest = build_training_sample(
        list(reversed(records)), token_budget=8, seed=5
    )

    assert [record.record_id for record in sample] == [
        record.record_id for record in reversed_sample
    ]
    assert manifest.sample_manifest_hash == reversed_manifest.sample_manifest_hash
    assert manifest.selected_document_ids != ["r0", "r1", "r2", "r3"]
