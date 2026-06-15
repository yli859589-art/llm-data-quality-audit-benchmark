from __future__ import annotations

from dataaudit_lm.data.records import make_record
from dataaudit_lm.filters.minhash_dedup import apply_minhash_near_dedup


def test_minhash_near_dedup_clusters_light_rewrites_but_not_unrelated_texts() -> None:
    records = [
        make_record(
            record_id="a",
            source_row_id="0",
            text="alpha beta gamma delta epsilon",
            source_dataset="toy",
            source_revision="r",
        ),
        make_record(
            record_id="b",
            source_row_id="1",
            text="alpha beta gamma delta zeta",
            source_dataset="toy",
            source_revision="r",
        ),
        make_record(
            record_id="c",
            source_row_id="2",
            text="finance markets coffee river",
            source_dataset="toy",
            source_revision="r",
        ),
    ]

    result = apply_minhash_near_dedup(records, threshold=0.4, ngram_size=2)

    assert result.kept_ids == ["a", "c"]
    assert len(result.manifest["clusters"]) == 2
    assert (
        result.kept_ids
        == apply_minhash_near_dedup(list(reversed(records)), threshold=0.4, ngram_size=2).kept_ids
    )
