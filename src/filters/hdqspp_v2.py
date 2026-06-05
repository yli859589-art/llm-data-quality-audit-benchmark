from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, replace

from analysis.quality_error_analysis import document_metrics, tokenize
from course_project_suite.llm_benchmark.quality import QualityWeights, score_document


@dataclass(frozen=True)
class HDQSv2Config:
    retention_ratio: float = 0.85
    base_quality_weight: float = 0.42
    length_distribution_weight: float = 0.18
    token_frequency_weight: float = 0.18
    quality_diversity_weight: float = 0.14
    repetition_weight: float = 0.08
    distribution_preserving_selection: bool = True
    use_length_prior: bool = True
    use_token_frequency: bool = True
    use_repetition_penalty: bool = True
    use_quality_diversity_balance: bool = True
    selection_mode: str = "distribution_preserving"


@dataclass(frozen=True)
class HDQSv2Score:
    index: int
    score: float
    components: dict[str, float]


V2_BASE_WEIGHTS = QualityWeights(
    lexical_diversity=0.9,
    char_entropy=0.8,
    token_entropy=0.8,
    repetition_penalty=0.45,
    ngram_repetition_penalty=0.35,
    pii_density_penalty=1.0,
    url_html_noise_penalty=0.45,
    non_linguistic_symbol_penalty=0.25,
    length_prior=0.25,
    language_consistency=0.6,
    optional_lm_surprisal=0.0,
    duplicate_cluster_penalty=0.0,
)


def config_from_mapping(payload: dict[str, object] | None) -> HDQSv2Config:
    if not payload:
        return HDQSv2Config()
    allowed = set(asdict(HDQSv2Config()))
    clean = {key: value for key, value in payload.items() if key in allowed}
    return HDQSv2Config(**clean)


def variant_config(config: HDQSv2Config, variant: str) -> HDQSv2Config:
    normalized = variant.casefold()
    if normalized in {"hdqspp_v2", "hdqs++v2", "full", "hdqspp_v2_full"}:
        return config
    if normalized == "v2_without_length_prior":
        return replace(config, use_length_prior=False, length_distribution_weight=0.0)
    if normalized == "v2_without_distribution_preservation":
        return replace(config, distribution_preserving_selection=False)
    if normalized == "v2_without_token_frequency_preservation":
        return replace(config, use_token_frequency=False, token_frequency_weight=0.0)
    if normalized == "v2_without_repetition_penalty":
        return replace(config, use_repetition_penalty=False, repetition_weight=0.0)
    if normalized == "v2_without_quality_diversity_balance":
        return replace(config, use_quality_diversity_balance=False, quality_diversity_weight=0.0)
    if normalized == "v2_hard_filtering":
        return replace(config, retention_ratio=0.6, distribution_preserving_selection=False)
    if normalized == "v2_soft_weighting_curriculum":
        return replace(config, retention_ratio=max(config.retention_ratio, 0.9))
    raise ValueError(f"Unknown HDQS++ v2 variant: {variant}")


def _length_bins(documents: list[str]) -> list[int]:
    token_lengths = sorted(len(tokenize(document)) for document in documents)
    if not token_lengths:
        return [0, 10**9]
    quantiles = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    bins = [0]
    for quantile in quantiles[1:-1]:
        index = min(len(token_lengths) - 1, max(0, int(quantile * len(token_lengths))))
        bins.append(max(bins[-1] + 1, token_lengths[index]))
    bins.append(10**9)
    return bins


def _bin_for_length(length: int, bins: list[int]) -> str:
    for low, high in zip(bins, bins[1:], strict=False):
        if low <= length < high:
            return f"{low}-{high}"
    return f"{bins[-2]}-{bins[-1]}"


def _reference_top_tokens(reference_documents: list[str], top_k: int = 1500) -> set[str]:
    counter: Counter[str] = Counter()
    for document in reference_documents:
        counter.update(tokenize(document))
    return {token for token, _ in counter.most_common(top_k)}


def score_hdqspp_v2(
    documents: list[str],
    *,
    reference_documents: list[str],
    config: HDQSv2Config | None = None,
) -> list[HDQSv2Score]:
    config = config or HDQSv2Config()
    bins = _length_bins(reference_documents or documents)
    reference_tokens = _reference_top_tokens(reference_documents or documents)
    scored = []
    total_weight = (
        config.base_quality_weight
        + config.length_distribution_weight
        + config.token_frequency_weight
        + config.quality_diversity_weight
        + config.repetition_weight
    )
    for index, document in enumerate(documents):
        base_score, base_components = score_document(document, V2_BASE_WEIGHTS)
        metrics = document_metrics(document)
        tokens = tokenize(document)
        token_overlap = (
            sum(1 for token in tokens if token in reference_tokens) / max(1, len(tokens))
            if config.use_token_frequency
            else 1.0
        )
        length_bin = _bin_for_length(len(tokens), bins)
        length_score = 1.0
        if config.use_length_prior:
            length_score = 0.75 + 0.25 * min(1.0, math.log1p(len(tokens)) / math.log1p(1200))
        repetition_score = 1.0
        if config.use_repetition_penalty:
            repetition_score = max(0.45, 1.0 - metrics["repetition_rate"])
        quality_diversity = (
            0.5 * base_score
            + 0.25 * min(1.0, metrics["token_entropy"] / 8.0)
            + 0.25 * metrics["token_diversity"]
            if config.use_quality_diversity_balance
            else 1.0
        )
        components = {
            **base_components,
            "v2_base_quality": base_score,
            "v2_length_distribution_match": length_score,
            "v2_token_frequency_preservation": token_overlap,
            "v2_quality_diversity_balance": quality_diversity,
            "v2_repetition_capped": repetition_score,
            "v2_length_bin": length_bin,
        }
        score = (
            config.base_quality_weight * base_score
            + config.length_distribution_weight * length_score
            + config.token_frequency_weight * token_overlap
            + config.quality_diversity_weight * quality_diversity
            + config.repetition_weight * repetition_score
        ) / max(1e-12, total_weight)
        scored.append(
            HDQSv2Score(
                index=index,
                score=max(0.0, min(1.0, score)),
                components=components,
            )
        )
    return scored


def _distribution_preserving_indices(
    scored: list[HDQSv2Score],
    documents: list[str],
    keep_count: int,
) -> set[int]:
    bins: dict[str, list[HDQSv2Score]] = defaultdict(list)
    for row in scored:
        bins[str(row.components["v2_length_bin"])].append(row)
    selected: set[int] = set()
    for rows in bins.values():
        quota = int(round(len(rows) * keep_count / max(1, len(scored))))
        if quota == 0 and rows and len(selected) < keep_count:
            quota = 1
        for row in sorted(rows, key=lambda item: item.score, reverse=True)[:quota]:
            selected.add(row.index)
    ranked = sorted(scored, key=lambda item: item.score, reverse=True)
    for row in ranked:
        if len(selected) >= keep_count:
            break
        selected.add(row.index)
    if len(selected) > keep_count:
        ranked_selected = sorted(
            (row for row in scored if row.index in selected),
            key=lambda item: item.score,
            reverse=True,
        )
        selected = {row.index for row in ranked_selected[:keep_count]}
    return selected


def select_hdqspp_v2(
    documents: list[str],
    *,
    reference_documents: list[str],
    config: HDQSv2Config | None = None,
    variant: str = "hdqspp_v2",
) -> tuple[list[str], list[HDQSv2Score]]:
    config = variant_config(config or HDQSv2Config(), variant)
    if not 0 < config.retention_ratio <= 1:
        raise ValueError("HDQS++ v2 retention_ratio must be in (0, 1].")
    scored = score_hdqspp_v2(documents, reference_documents=reference_documents, config=config)
    keep_count = max(1, math.ceil(len(scored) * config.retention_ratio))
    if config.distribution_preserving_selection:
        selected_indices = _distribution_preserving_indices(scored, documents, keep_count)
    else:
        selected_indices = {
            row.index
            for row in sorted(scored, key=lambda item: item.score, reverse=True)[
                :keep_count
            ]
        }
    selected = [document for index, document in enumerate(documents) if index in selected_indices]
    return selected, scored
