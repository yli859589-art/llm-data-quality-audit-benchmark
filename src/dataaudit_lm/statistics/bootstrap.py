from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class BootstrapCI:
    mean: float
    lower: float
    upper: float
    samples: int


def bootstrap_mean_ci(
    values: list[float],
    *,
    samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 0,
) -> BootstrapCI:
    if not values:
        raise ValueError("values must not be empty")
    rng = random.Random(seed)
    means = []
    for _ in range(samples):
        draw = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(draw) / len(draw))
    means.sort()
    lower_idx = max(0, int((alpha / 2) * samples))
    upper_idx = min(samples - 1, int((1 - alpha / 2) * samples))
    return BootstrapCI(sum(values) / len(values), means[lower_idx], means[upper_idx], samples)
