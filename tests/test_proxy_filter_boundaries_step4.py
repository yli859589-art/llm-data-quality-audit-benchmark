from __future__ import annotations

from filters_v2.base import FilterConfig, FilterInput
from filters_v2.c4_style import C4StyleProxyFilter
from filters_v2.ccnet_style import CCNetStyleProxyFilter
from filters_v2.classifier_proxy import ClassifierQualityProxyFilter
from filters_v2.embedding_diversity_proxy import EmbeddingDiversityProxyFilter
from filters_v2.gopher_style import GopherStyleProxyFilter
from filters_v2.hdqspp_wrappers import HDQSppHistoricalFilter
from filters_v2.minhash_dedup import MinHashNearDedupProxyFilter
from filters_v2.perplexity_proxy import PerplexityProxyFilter


def _records() -> list[FilterInput]:
    return [
        FilterInput("a", "The clean document has normal words and useful context.", estimated_tokens=9),
        FilterInput("b", "The clean document has normal words and useful context.", estimated_tokens=9),
        FilterInput("c", "<html> $$$ http://example.com 123456789", estimated_tokens=4),
    ]


def _config(name: str, filter_type: str, target_keep_rate: float | None = None) -> FilterConfig:
    return FilterConfig(
        filter_name=name,
        filter_type=filter_type,
        target_keep_rate=target_keep_rate,
        allow_proxy=True,
        dataset_manifest_path="artifacts/data_step2/wikitext2_smoke/data_manifest.json",
        tokenizer_manifest_path="artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
    )


def test_proxy_filters_label_proxy_used_true() -> None:
    proxy_classes = [
        (MinHashNearDedupProxyFilter, "minhash_near_dedup", "minhash_near_dedup_proxy"),
        (C4StyleProxyFilter, "c4_style_proxy", "c4_style_proxy"),
        (GopherStyleProxyFilter, "gopher_style_proxy", "gopher_style_proxy"),
        (CCNetStyleProxyFilter, "ccnet_style_protocol", "ccnet_style_proxy"),
        (PerplexityProxyFilter, "perplexity_proxy", "perplexity_proxy"),
        (ClassifierQualityProxyFilter, "classifier_proxy_protocol", "classifier_quality_proxy"),
        (EmbeddingDiversityProxyFilter, "embedding_diversity_proxy", "embedding_diversity_proxy"),
    ]
    for cls, name, filter_type in proxy_classes:
        instance = cls(_config(name, filter_type, target_keep_rate=0.67))
        result = instance.filter(_records())
        assert instance.proxy_used is True
        assert result.summary["proxy_used"] is True


def test_ccnet_and_classifier_do_not_claim_real_external_baselines() -> None:
    ccnet = CCNetStyleProxyFilter(_config("ccnet_style_protocol", "ccnet_style_proxy"))
    classifier = ClassifierQualityProxyFilter(_config("classifier_proxy_protocol", "classifier_quality_proxy"))

    assert ccnet.external_dependency_available is False
    assert ccnet.official_reproduction is False
    result = classifier.filter(_records())
    assert result.decisions[0].metadata["trained_classifier_artifact"] == ""


def test_hdqspp_is_historical_failure_analysis_object() -> None:
    hdqspp = HDQSppHistoricalFilter(_config("hdqspp_historical", "hdqspp_historical"))
    result = hdqspp.filter(_records())

    assert hdqspp.historical_baseline is True
    assert result.summary["historical_baseline"] is True
    assert result.decisions[0].metadata["failure_analysis_object"] is True
