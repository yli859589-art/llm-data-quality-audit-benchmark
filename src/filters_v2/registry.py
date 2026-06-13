from __future__ import annotations

from .c4_style import C4StyleProxyFilter
from .ccnet_style import CCNetStyleProxyFilter
from .classifier_proxy import ClassifierQualityProxyFilter
from .embedding_diversity_proxy import EmbeddingDiversityProxyFilter
from .exact_dedup import ExactDedupFilter
from .gopher_style import GopherStyleProxyFilter
from .hdqspp_wrappers import HDQSppHistoricalFilter
from .length_filter import LengthFilter
from .minhash_dedup import MinHashNearDedupProxyFilter
from .perplexity_proxy import PerplexityProxyFilter
from .random_keep_rate import RandomSameKeepRateFilter
from .raw import RawFilter
from .urd_selector import URDSelectorFilter

FILTER_REGISTRY = {
    "raw": RawFilter,
    "random_same_keep_rate": RandomSameKeepRateFilter,
    "exact_dedup": ExactDedupFilter,
    "dedup_only": ExactDedupFilter,
    "minhash_near_dedup": MinHashNearDedupProxyFilter,
    "minhash_dedup_proxy": MinHashNearDedupProxyFilter,
    "length_filter": LengthFilter,
    "hdqspp_historical": HDQSppHistoricalFilter,
    "hdqspp": HDQSppHistoricalFilter,
    "hdqspp_v2": HDQSppHistoricalFilter,
    "hdqspp_v3": HDQSppHistoricalFilter,
    "c4_style_proxy": C4StyleProxyFilter,
    "gopher_style_proxy": GopherStyleProxyFilter,
    "ccnet_style_protocol": CCNetStyleProxyFilter,
    "ccnet_style_proxy": CCNetStyleProxyFilter,
    "perplexity_proxy": PerplexityProxyFilter,
    "classifier_proxy_protocol": ClassifierQualityProxyFilter,
    "classifier_quality_proxy": ClassifierQualityProxyFilter,
    "embedding_diversity_proxy": EmbeddingDiversityProxyFilter,
    "urd_fixed": URDSelectorFilter,
    "urd_pareto": URDSelectorFilter,
    "urd_ablation_no_utility": URDSelectorFilter,
    "urd_ablation_no_risk": URDSelectorFilter,
    "urd_ablation_no_diversity": URDSelectorFilter,
    "urd_ablation_no_shift": URDSelectorFilter,
    "urd_ablation_no_cost": URDSelectorFilter,
}


def available_filters() -> list[str]:
    return sorted(FILTER_REGISTRY)


def get_filter_class(name: str):
    try:
        return FILTER_REGISTRY[name]
    except KeyError as exc:
        raise ValueError(f"Unknown filter: {name}") from exc
