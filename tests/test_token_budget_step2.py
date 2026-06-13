from __future__ import annotations

from data_sources.records import DatasetRecord
from data_sources.token_budget import (
    estimate_text_tokens,
    parse_token_budget,
    select_records_to_budget,
)


def _records() -> list[DatasetRecord]:
    return [
        DatasetRecord("a", "one two", "unit", "train", {}),
        DatasetRecord("b", "three four five", "unit", "train", {}),
        DatasetRecord("c", "six", "unit", "train", {}),
    ]


def test_parse_token_budget_units() -> None:
    assert parse_token_budget("full") is None
    assert parse_token_budget("1K") == 1_000
    assert parse_token_budget("10K") == 10_000
    assert parse_token_budget("1M") == 1_000_000
    assert parse_token_budget("50M") == 50_000_000
    assert parse_token_budget("100M") == 100_000_000
    assert parse_token_budget("500M") == 500_000_000
    assert parse_token_budget("1B") == 1_000_000_000
    assert parse_token_budget("123") == 123
    assert parse_token_budget(7) == 7


def test_estimate_text_tokens_proxy_types() -> None:
    assert estimate_text_tokens("one two three", "whitespace") == 3
    assert estimate_text_tokens("abcd", "character") == 4
    assert estimate_text_tokens("future", "unknown") == 0
    assert estimate_text_tokens("future", "future_bpe") == 0


def test_select_records_to_budget_is_deterministic() -> None:
    first = select_records_to_budget(_records(), "full", seed=42, shuffle=True)
    second = select_records_to_budget(_records(), "full", seed=42, shuffle=True)
    assert [record.doc_id for record in first] == [record.doc_id for record in second]


def test_select_records_to_budget_respects_document_order_budget() -> None:
    selected = select_records_to_budget(_records(), 5, seed=1, shuffle=False)
    assert [record.doc_id for record in selected] == ["a", "b"]
