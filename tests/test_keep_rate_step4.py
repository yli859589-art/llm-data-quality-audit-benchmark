from __future__ import annotations

from filters_v2.keep_rate import (
    compute_document_keep_rate,
    compute_token_keep_rate,
    keep_count_for_rate,
    select_top_k_by_keep_rate,
    validate_keep_rate,
)


def test_keep_rate_utilities_record_document_and_token_rates() -> None:
    assert compute_document_keep_rate(4, 2) == 0.5
    assert compute_token_keep_rate(100, 40) == 0.4
    assert keep_count_for_rate(3, 0.5) == 2


def test_select_top_k_by_keep_rate_is_score_ordered() -> None:
    selected = select_top_k_by_keep_rate(["a", "b", "c"], [0.2, 0.9, 0.5], 0.5)

    assert selected == {1, 2}


def test_validate_keep_rate_explains_integer_mismatch() -> None:
    report = validate_keep_rate(2 / 3, 0.5, tolerance=0.2)

    assert report["status"] == "passed"
    assert "integer document counts" in str(report["reason"])
