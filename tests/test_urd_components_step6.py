from __future__ import annotations

from filters_v2.base import FilterInput
from filters_v2.urd_components import score_cost, score_diversity, score_risk, score_shift, score_utility


def _records() -> list[FilterInput]:
    return [
        FilterInput("a", "alpha beta gamma alpha", source="wiki", estimated_tokens=4),
        FilterInput("b", "visit https://example.com <p>noise</p> 12345", source="web", estimated_tokens=5),
        FilterInput("c", "delta epsilon zeta useful text", source="wiki", estimated_tokens=5),
    ]


def _assert_score_range(payload: dict[str, object], field: str) -> None:
    value = payload[field]
    assert isinstance(value, (int, float))
    assert 0.0 <= float(value) <= 1.0


def test_urd_component_scores_are_normalized() -> None:
    records = _records()
    record = records[0]

    _assert_score_range(score_utility(record, records), "utility_score")
    _assert_score_range(score_risk(record, records), "risk_score")
    _assert_score_range(score_diversity(record, records), "diversity_score")
    _assert_score_range(score_shift(record, records), "shift_penalty")
    _assert_score_range(score_cost(record, records), "cost_score")


def test_urd_components_are_marked_as_proxies() -> None:
    records = _records()
    record = records[1]

    assert score_utility(record, records)["utility_proxy_used"] is True
    assert score_risk(record, records)["risk_proxy_used"] is True
    assert score_diversity(record, records)["diversity_proxy_used"] is True
    assert score_shift(record, records)["shift_proxy_used"] is True
    assert score_cost(record, records)["cost_proxy_used"] is True
