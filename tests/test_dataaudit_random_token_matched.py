from __future__ import annotations

from dataaudit_lm.data.records import make_record
from dataaudit_lm.filters.random_matched import apply_random_token_matched


def test_random_token_matched_hits_target_when_feasible_and_is_order_invariant() -> None:
    records = [
        make_record(
            record_id="a",
            source_row_id="0",
            text="a " * 3,
            source_dataset="toy",
            source_revision="r",
            token_count=3,
        ),
        make_record(
            record_id="b",
            source_row_id="1",
            text="b " * 4,
            source_dataset="toy",
            source_revision="r",
            token_count=4,
        ),
        make_record(
            record_id="c",
            source_row_id="2",
            text="c " * 7,
            source_dataset="toy",
            source_revision="r",
            token_count=7,
        ),
    ]

    result = apply_random_token_matched(records, target_tokens=7, seed=13, target_name="length")
    reversed_result = apply_random_token_matched(
        list(reversed(records)), target_tokens=7, seed=13, target_name="length"
    )

    assert result.manifest["selected_tokens"] == 7
    assert result.manifest["within_tolerance"] is True
    assert result.kept_ids == reversed_result.kept_ids
