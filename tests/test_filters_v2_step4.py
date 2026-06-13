from __future__ import annotations

from filters_v2.base import FilterConfig, FilterInput
from filters_v2.exact_dedup import ExactDedupFilter
from filters_v2.length_filter import LengthFilter
from filters_v2.random_keep_rate import RandomSameKeepRateFilter
from filters_v2.raw import RawFilter


def _records() -> list[FilterInput]:
    return [
        FilterInput("a", "alpha beta gamma", estimated_tokens=3),
        FilterInput("b", "alpha beta gamma", estimated_tokens=3),
        FilterInput("c", "short", estimated_tokens=1),
    ]


def _config(name: str, filter_type: str, **kwargs) -> FilterConfig:
    return FilterConfig(
        filter_name=name,
        filter_type=filter_type,
        target_keep_rate=kwargs.pop("target_keep_rate", None),
        seed=kwargs.pop("seed", 42),
        params=kwargs.pop("params", {}),
        dataset_manifest_path="artifacts/data_step2/wikitext2_smoke/data_manifest.json",
        tokenizer_manifest_path="artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
        **kwargs,
    )


def test_raw_keeps_all_records() -> None:
    result = RawFilter(_config("raw", "raw")).filter(_records())

    assert result.kept_docs == result.input_docs
    assert all(decision.reason == "raw_keep_all" for decision in result.decisions)


def test_random_same_keep_rate_is_deterministic() -> None:
    config = _config("random_same_keep_rate", "random_same_keep_rate", target_keep_rate=0.5, seed=7)
    left = RandomSameKeepRateFilter(config).filter(_records())
    right = RandomSameKeepRateFilter(config).filter(_records())

    assert [decision.to_dict() for decision in left.decisions] == [
        decision.to_dict() for decision in right.decisions
    ]
    assert left.kept_docs == 2


def test_exact_dedup_removes_duplicate_text() -> None:
    result = ExactDedupFilter(_config("exact_dedup", "exact_dedup")).filter(_records())

    assert result.kept_docs == 2
    assert any(decision.reason == "exact_duplicate_removed" for decision in result.decisions)


def test_length_filter_respects_min_and_max() -> None:
    config = _config(
        "length_filter",
        "length_filter",
        params={"min_estimated_tokens": 2, "max_estimated_tokens": 4},
    )
    result = LengthFilter(config).filter(_records())

    assert result.kept_docs == 2
    assert result.decisions[-1].reason == "length_below_min"
