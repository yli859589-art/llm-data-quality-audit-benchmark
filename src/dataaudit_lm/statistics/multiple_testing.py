from __future__ import annotations


def holm_bonferroni(p_values: list[float]) -> list[float]:
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    total = len(p_values)
    for rank, (index, p_value) in enumerate(indexed):
        running = max(running, min(1.0, (total - rank) * p_value))
        adjusted[index] = running
    return adjusted
