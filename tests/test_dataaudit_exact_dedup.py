from __future__ import annotations

from dataaudit_lm.data.records import make_record
from dataaudit_lm.filters.exact_dedup import apply_exact_dedup


def test_exact_dedup_selects_stable_representative_independent_of_input_order() -> None:
    records = [
        make_record(
            record_id="b", source_row_id="1", text="dup", source_dataset="toy", source_revision="r"
        ),
        make_record(
            record_id="a", source_row_id="0", text="dup", source_dataset="toy", source_revision="r"
        ),
        make_record(
            record_id="c",
            source_row_id="2",
            text="unique",
            source_dataset="toy",
            source_revision="r",
        ),
    ]

    result = apply_exact_dedup(records)
    reversed_result = apply_exact_dedup(list(reversed(records)))

    assert result.kept_ids == reversed_result.kept_ids == ["a", "c"]
    assert result.manifest["duplicate_count"] == 1
    assert result.manifest["method_role"] == "INDEPENDENT_FILTER"
