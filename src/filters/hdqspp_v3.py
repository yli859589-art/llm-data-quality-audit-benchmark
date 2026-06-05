from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import asdict, dataclass, replace

from analysis.quality_error_analysis import document_metrics, tokenize
from course_project_suite.llm_benchmark.quality import QualityWeights, score_document


@dataclass(frozen=True)
class HDQSv3Config:
    retention_ratio: float = 0.85
    base_quality_weight: float = 0.55
    quality_diversity_weight: float = 0.23
    repetition_weight: float = 0.14
    weak_length_guardrail_weight: float = 0.08
    token_frequency_weight: float = 0.0
    use_token_frequency: bool = False
    use_quality_diversity_balance: bool = True
    use_repetition_penalty: bool = True
    use_length_guardrails: bool = True
    selection_mode: str = "calibrated_soft_curriculum"
    deterministic_top_fraction: float = 0.72
    soft_sampling_temperature: float = 0.20
    min_bin_retention_fraction: float = 0.45
    curriculum_order: str = "score_interleave"
    seed: int = 0


@dataclass(frozen=True)
class HDQSv3Score:
    index: int
    score: float
    components: dict[str, float]


V3_BASE_WEIGHTS = QualityWeights(
    lexical_diversity=0.95,
    char_entropy=0.75,
    token_entropy=0.85,
    repetition_penalty=0.65,
    ngram_repetition_penalty=0.55,
    pii_density_penalty=1.0,
    url_html_noise_penalty=0.55,
    non_linguistic_symbol_penalty=0.35,
    length_prior=0.05,
    language_consistency=0.6,
    optional_lm_surprisal=0.0,
    duplicate_cluster_penalty=0.0,
)


def config_from_mapping(payload: dict[str, object] | None) -> HDQSv3Config:
    if not payload:
        return HDQSv3Config()
    allowed = set(asdict(HDQSv3Config()))
    clean = {key: value for key, value in payload.items() if key in allowed}
    return HDQSv3Config(**clean)


def variant_config(config: HDQSv3Config, variant: str) -> HDQSv3Config:
    normalized = variant.casefold()
    if normalized in {"hdqspp_v3", "hdqs++v3", "full", "v3_full", "hdqspp_v3_full"}:
        return config
    if normalized == "v3_without_soft_weighting":
        return replace(
            config,
            selection_mode="score_rank",
            deterministic_top_fraction=1.0,
            curriculum_order="original",
        )
    if normalized == "v3_without_keep_rate_calibration":
        return replace(config, retention_ratio=0.6)
    if normalized == "v3_without_quality_diversity_balance":
        return replace(config, use_quality_diversity_balance=False, quality_diversity_weight=0.0)
    if normalized == "v3_hard_filtering_only":
        return replace(
            config,
            retention_ratio=0.6,
            base_quality_weight=1.0,
            quality_diversity_weight=0.0,
            repetition_weight=0.0,
            weak_length_guardrail_weight=0.0,
            selection_mode="score_rank",
            deterministic_top_fraction=1.0,
            use_length_guardrails=False,
            curriculum_order="original",
        )
    if normalized == "v3_soft_weighting_only":
        return replace(
            config,
            retention_ratio=1.0,
            selection_mode="score_rank",
            deterministic_top_fraction=1.0,
            curriculum_order="score_interleave",
        )
    if normalized == "v3_without_length_guardrails":
        return replace(config, use_length_guardrails=False, weak_length_guardrail_weight=0.0)
    if normalized == "v3_without_repetition_penalty":
        return replace(config, use_repetition_penalty=False, repetition_weight=0.0)
    raise ValueError(f"Unknown HDQS++ v3 variant: {variant}")


def _length_bins(documents: list[str]) -> list[int]:
    lengths = sorted(len(tokenize(document)) for document in documents)
    if not lengths:
        return [0, 10**9]
    bins = [0]
    for quantile in [0.2, 0.4, 0.6, 0.8]:
        index = min(len(lengths) - 1, max(0, int(quantile * len(lengths))))
        bins.append(max(bins[-1] + 1, lengths[index]))
    bins.append(10**9)
    return bins


def _bin_for_length(length: int, bins: list[int]) -> str:
    for low, high in zip(bins, bins[1:], strict=False):
        if low <= length < high:
            return f"{low}-{high}"
    return f"{bins[-2]}-{bins[-1]}"


def _length_guardrail_score(length: int, reference_lengths: list[int]) -> float:
    if not reference_lengths:
        return 1.0
    midpoint = reference_lengths[len(reference_lengths) // 2]
    low = reference_lengths[max(0, int(0.1 * (len(reference_lengths) - 1)))]
    high = reference_lengths[min(len(reference_lengths) - 1, int(0.9 * (len(reference_lengths) - 1)))]
    span = max(1.0, math.log1p(high) - math.log1p(low))
    distance = abs(math.log1p(length) - math.log1p(midpoint)) / span
    return max(0.0, min(1.0, 1.0 - 0.5 * distance))


def score_hdqspp_v3(
    documents: list[str],
    *,
    reference_documents: list[str],
    config: HDQSv3Config | None = None,
) -> list[HDQSv3Score]:
    config = config or HDQSv3Config()
    reference = reference_documents or documents
    reference_lengths = sorted(len(tokenize(document)) for document in reference)
    bins = _length_bins(documents)
    total_weight = (
        config.base_quality_weight
        + config.quality_diversity_weight
        + config.repetition_weight
        + config.weak_length_guardrail_weight
        + config.token_frequency_weight
    )
    scored: list[HDQSv3Score] = []
    for index, document in enumerate(documents):
        base_score, base_components = score_document(document, V3_BASE_WEIGHTS)
        metrics = document_metrics(document)
        tokens = tokenize(document)
        quality_diversity = (
            0.50 * base_score
            + 0.25 * min(1.0, metrics["token_entropy"] / 8.0)
            + 0.25 * metrics["token_diversity"]
            if config.use_quality_diversity_balance
            else 1.0
        )
        repetition_score = (
            max(0.50, 1.0 - metrics["repetition_rate"])
            if config.use_repetition_penalty
            else 1.0
        )
        length_guardrail = (
            _length_guardrail_score(len(tokens), reference_lengths)
            if config.use_length_guardrails
            else 1.0
        )
        token_frequency = 1.0
        components = {
            **base_components,
            "v3_base_quality": base_score,
            "v3_quality_diversity_balance": quality_diversity,
            "v3_repetition_capped": repetition_score,
            "v3_weak_length_guardrail": length_guardrail,
            "v3_token_frequency_disabled": 1.0 if not config.use_token_frequency else token_frequency,
            "v3_length_bin": _bin_for_length(len(tokens), bins),
        }
        score = (
            config.base_quality_weight * base_score
            + config.quality_diversity_weight * quality_diversity
            + config.repetition_weight * repetition_score
            + config.weak_length_guardrail_weight * length_guardrail
            + config.token_frequency_weight * token_frequency
        ) / max(1e-12, total_weight)
        scored.append(
            HDQSv3Score(
                index=index,
                score=max(0.0, min(1.0, score)),
                components=components,
            )
        )
    return scored


def _weighted_soft_fill(
    candidates: list[HDQSv3Score],
    count: int,
    *,
    temperature: float,
    rng: random.Random,
) -> list[HDQSv3Score]:
    pool = list(candidates)
    selected: list[HDQSv3Score] = []
    temperature = max(temperature, 1e-6)
    while pool and len(selected) < count:
        weights = [math.exp((row.score - 1.0) / temperature) for row in pool]
        total = sum(weights)
        draw = rng.random() * total
        cursor = 0.0
        picked_index = 0
        for index, weight in enumerate(weights):
            cursor += weight
            if cursor >= draw:
                picked_index = index
                break
        selected.append(pool.pop(picked_index))
    return selected


def _weak_length_rebalance(
    selected: set[int],
    scored: list[HDQSv3Score],
    keep_count: int,
    config: HDQSv3Config,
) -> set[int]:
    if not config.use_length_guardrails:
        return selected
    by_bin: dict[str, list[HDQSv3Score]] = defaultdict(list)
    for row in scored:
        by_bin[str(row.components["v3_length_bin"])].append(row)
    current_counts: dict[str, int] = defaultdict(int)
    for row in scored:
        if row.index in selected:
            current_counts[str(row.components["v3_length_bin"])] += 1
    selected_rows = {row.index: row for row in scored if row.index in selected}
    for bin_name, rows in by_bin.items():
        expected = len(rows) * keep_count / max(1, len(scored))
        floor = int(math.floor(expected * config.min_bin_retention_fraction))
        if floor <= 0 or current_counts[bin_name] >= floor:
            continue
        needed = floor - current_counts[bin_name]
        additions = [
            row
            for row in sorted(rows, key=lambda item: item.score, reverse=True)
            if row.index not in selected
        ][:needed]
        for row in additions:
            if len(selected) >= keep_count:
                removable = sorted(selected_rows.values(), key=lambda item: item.score)[0]
                selected.remove(removable.index)
                selected_rows.pop(removable.index, None)
            selected.add(row.index)
            selected_rows[row.index] = row
    return selected


def _curriculum_order(
    selected: list[HDQSv3Score],
    *,
    config: HDQSv3Config,
) -> list[int]:
    if config.curriculum_order == "original":
        return sorted(row.index for row in selected)
    ranked = sorted(selected, key=lambda item: item.score, reverse=True)
    high = ranked[::2]
    low = list(reversed(ranked[1::2]))
    interleaved: list[int] = []
    for left, right in zip(high, low, strict=False):
        interleaved.append(left.index)
        interleaved.append(right.index)
    longer = high if len(high) > len(low) else low
    interleaved.extend(row.index for row in longer[len(interleaved) // 2 :])
    return interleaved


def select_hdqspp_v3(
    documents: list[str],
    *,
    reference_documents: list[str],
    config: HDQSv3Config | None = None,
    variant: str = "hdqspp_v3",
    seed: int | None = None,
) -> tuple[list[str], list[HDQSv3Score]]:
    config = variant_config(config or HDQSv3Config(), variant)
    if not 0 < config.retention_ratio <= 1:
        raise ValueError("HDQS++ v3 retention_ratio must be in (0, 1].")
    scored = score_hdqspp_v3(documents, reference_documents=reference_documents, config=config)
    keep_count = max(1, math.ceil(len(scored) * config.retention_ratio))
    ranked = sorted(scored, key=lambda item: item.score, reverse=True)
    if config.selection_mode == "score_rank" or keep_count >= len(scored):
        selected = ranked[:keep_count]
    elif config.selection_mode == "calibrated_soft_curriculum":
        top_count = max(1, min(keep_count, int(round(keep_count * config.deterministic_top_fraction))))
        deterministic = ranked[:top_count]
        selected_indices = {row.index for row in deterministic}
        remaining = [row for row in ranked if row.index not in selected_indices]
        rng = random.Random(config.seed if seed is None else seed)
        soft = _weighted_soft_fill(
            remaining,
            keep_count - top_count,
            temperature=config.soft_sampling_temperature,
            rng=rng,
        )
        selected = deterministic + soft
    else:
        raise ValueError(f"Unknown HDQS++ v3 selection_mode: {config.selection_mode}")
    selected_indices = _weak_length_rebalance(
        {row.index for row in selected},
        scored,
        keep_count,
        config,
    )
    selected_rows = [row for row in scored if row.index in selected_indices]
    ordered_indices = _curriculum_order(selected_rows, config=config)
    selected_documents = [documents[index] for index in ordered_indices]
    return selected_documents, scored
