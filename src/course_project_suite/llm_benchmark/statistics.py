from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict
from typing import Any


def summarize(values: list[float]) -> dict[str, float | int | None]:
    if not values:
        raise ValueError("Cannot summarize an empty sequence.")
    mean = statistics.mean(values)
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    margin = 1.96 * std / math.sqrt(len(values)) if len(values) > 1 else None
    return {
        "count": len(values),
        "mean": mean,
        "std": std,
        "ci95_low": mean - margin if margin is not None else None,
        "ci95_high": mean + margin if margin is not None else None,
    }


def bootstrap_mean_ci(
    values: list[float],
    *,
    samples: int = 1000,
    confidence: float = 0.95,
    seed: int = 13,
) -> dict[str, float | int]:
    if not values:
        raise ValueError("Cannot bootstrap an empty sequence.")
    if samples <= 0:
        raise ValueError("samples must be positive.")
    rng = random.Random(seed)
    means = []
    for _ in range(samples):
        draw = [values[rng.randrange(len(values))] for _ in values]
        means.append(statistics.mean(draw))
    means.sort()
    alpha = (1 - confidence) / 2
    low_index = min(len(means) - 1, max(0, int(alpha * len(means))))
    high_index = min(len(means) - 1, max(0, int((1 - alpha) * len(means)) - 1))
    return {
        "count": len(values),
        "bootstrap_samples": samples,
        "confidence": confidence,
        "mean": statistics.mean(values),
        "ci_low": means[low_index],
        "ci_high": means[high_index],
    }


def paired_difference_summary(
    baseline: list[float],
    candidate: list[float],
    *,
    lower_is_better: bool = True,
) -> dict[str, float | int | bool | None]:
    if len(baseline) != len(candidate):
        raise ValueError("baseline and candidate must have the same length.")
    if not baseline:
        raise ValueError("Cannot compare empty sequences.")
    differences = [
        (left - right if lower_is_better else right - left)
        for left, right in zip(baseline, candidate, strict=True)
    ]
    summary = summarize(differences)
    return {
        **summary,
        "lower_is_better": lower_is_better,
        "positive_mean_improvement": bool(summary["mean"] is not None and summary["mean"] > 0),
    }


def aggregate_model_runs(
    runs: list[dict[str, Any]],
    *,
    metric: str = "final_val_perplexity",
    baseline_variant: str = "raw_noisy_baseline",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    seed_rows = [
        {
            "variant": str(run["variant"]),
            "seed": int(run["seed"]),
            "metric": metric,
            "value": float(run[metric]),
            "final_val_loss": float(run["final_val_loss"]),
            "next_char_accuracy": float(run["final_val_next_char_accuracy"]),
        }
        for run in runs
    ]
    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in seed_rows:
        by_variant[str(row["variant"])].append(row)
    aggregate_rows = []
    for variant, rows in sorted(by_variant.items()):
        values = [float(row["value"]) for row in rows]
        aggregate_rows.append(
            {
                "variant": variant,
                "metric": metric,
                **summarize(values),
                "bootstrap_ci_low": bootstrap_mean_ci(values, samples=200)["ci_low"],
                "bootstrap_ci_high": bootstrap_mean_ci(values, samples=200)["ci_high"],
            }
        )
    tests: dict[str, Any] = {"metric": metric, "baseline_variant": baseline_variant, "paired": {}}
    baseline_rows = sorted(by_variant.get(baseline_variant, []), key=lambda row: int(row["seed"]))
    baseline_values = [float(row["value"]) for row in baseline_rows]
    for variant, rows in sorted(by_variant.items()):
        if variant == baseline_variant:
            continue
        ordered = sorted(rows, key=lambda row: int(row["seed"]))
        if [row["seed"] for row in ordered] != [row["seed"] for row in baseline_rows]:
            tests["paired"][variant] = {"status": "skipped_seed_mismatch"}
            continue
        values = [float(row["value"]) for row in ordered]
        tests["paired"][variant] = paired_difference_summary(baseline_values, values)
    return seed_rows, aggregate_rows, tests
