from __future__ import annotations

from filters_v2.base import FilterConfig, FilterInput
from filters_v2.c4_style import C4StyleProxyFilter
from filters_v2.minhash_dedup import MinHashNearDedupProxyFilter
from filters_v2.registry import get_filter_class
from filters_v2.urd_selector import URDSelectorFilter


def _record(doc_id: str, text: str, tokens: int = 10, source: str = "example") -> FilterInput:
    return FilterInput(doc_id=doc_id, text=text, source=source, estimated_tokens=tokens)


def test_minhash_lsh_known_duplicate_clusters_are_stable_across_input_order() -> None:
    records = [
        _record("z", "the quick brown fox jumps over the lazy dog today"),
        _record("a", "the quick brown fox jumps over the lazy dog today"),
        _record("u", "quantum mechanics describes physical systems with equations"),
    ]
    config = FilterConfig(filter_name="minhash", filter_type="minhash_lsh_near_dedup", seed=7, params={"similarity_threshold": 0.9, "shingle_size": 2, "num_permutations": 64, "bands": 16})
    forward = MinHashNearDedupProxyFilter(config).filter(records)
    reverse = MinHashNearDedupProxyFilter(config).filter(list(reversed(records)))
    kept_forward = {item.doc_id for item in forward.decisions if item.keep}
    kept_reverse = {item.doc_id for item in reverse.decisions if item.keep}
    assert kept_forward == kept_reverse == {"a", "u"}
    assert forward.summary["all_pairs_avoided"] is True
    assert get_filter_class("minhash_lsh_near_dedup") is MinHashNearDedupProxyFilter


def test_quality_profile_rejects_empty_or_control_text_and_preserves_readable_text() -> None:
    filter_instance = C4StyleProxyFilter(FilterConfig(filter_name="c4", filter_type="c4_style_proxy", params={"min_quality_score": 0.25}))
    bad = filter_instance.score(_record("bad", "\x01\x02\x03"))
    good = filter_instance.score(_record("good", "This readable explanatory paragraph contains complete sentences and useful information."))
    assert not bad.keep
    assert good.keep
    assert good.metadata["component_scores"]["quality_profile"]["language"]["is_readable"] is True


def test_urd_respects_token_budget_and_records_budget_rejection() -> None:
    records = [_record("a", "useful diverse scientific explanation with details", 8), _record("b", "another readable explanation with examples", 8), _record("c", "short readable note", 3)]
    config = FilterConfig(filter_name="urd_fixed", filter_type="urd_selector", target_keep_rate=1.0, token_budget=11, params={"max_risk_score": 1.0})
    result = URDSelectorFilter(config).filter(records)
    kept_tokens = sum(record.estimated_tokens for record in records if next(item for item in result.decisions if item.doc_id == record.doc_id).keep)
    assert kept_tokens <= 11
    assert any("budget" in item.reason for item in result.decisions if not item.keep)
