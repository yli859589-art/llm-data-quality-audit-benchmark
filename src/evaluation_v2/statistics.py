from __future__ import annotations

import math
import random
from statistics import mean as _mean
from typing import Any


def safe_mean(values: list[float]) -> float | None:
    return _mean(values) if values else None


def safe_std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    m = _mean(values)
    return math.sqrt(sum((value - m) ** 2 for value in values) / (len(values) - 1))


def standard_error(values: list[float]) -> float | None:
    std = safe_std(values)
    return None if std is None else std / math.sqrt(len(values))


def bootstrap_ci(values: list[float], *, samples: int = 200, seed: int = 42) -> dict[str, Any]:
    if len(values) < 2:
        return {
            "ci95_low": None,
            "ci95_high": None,
            "warning": "insufficient_sample_size_for_bootstrap",
        }
    rng = random.Random(seed)
    means = []
    for _ in range(samples):
        draw = [values[rng.randrange(len(values))] for _ in values]
        means.append(_mean(draw))
    means.sort()
    low = means[int(0.025 * (len(means) - 1))]
    high = means[int(0.975 * (len(means) - 1))]
    return {"ci95_low": low, "ci95_high": high, "warning": ""}


def paired_difference(left: list[float], right: list[float]) -> dict[str, Any]:
    if len(left) != len(right) or not left:
        return {"mean_difference": None, "warning": "paired_inputs_missing_or_mismatched"}
    diffs = [a - b for a, b in zip(left, right)]
    return {"mean_difference": safe_mean(diffs), "std_difference": safe_std(diffs), "warning": ""}


def rank_correlation(left: list[float], right: list[float]) -> dict[str, Any]:
    if len(left) != len(right) or len(left) < 2:
        return {"spearman_proxy": None, "warning": "insufficient_sample_size_for_rank_correlation"}
    left_rank = {index: rank for rank, index in enumerate(sorted(range(len(left)), key=lambda item: left[item]))}
    right_rank = {index: rank for rank, index in enumerate(sorted(range(len(right)), key=lambda item: right[item]))}
    n = len(left)
    diff_sq = sum((left_rank[i] - right_rank[i]) ** 2 for i in range(n))
    return {"spearman_proxy": 1 - (6 * diff_sq) / (n * (n * n - 1)), "warning": ""}


def summary_stats(values: list[float]) -> dict[str, Any]:
    return {
        "mean": safe_mean(values),
        "std": safe_std(values),
        "standard_error": standard_error(values),
        "n": len(values),
        "insufficient_sample_warning": len(values) < 2,
    }
