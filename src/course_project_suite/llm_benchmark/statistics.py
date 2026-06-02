from __future__ import annotations

import math
import statistics


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
