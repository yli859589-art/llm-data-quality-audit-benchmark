from __future__ import annotations

import math


def cohens_d_paired(differences: list[float]) -> float:
    if len(differences) < 2:
        raise ValueError("at least two paired differences are required")
    mean = sum(differences) / len(differences)
    variance = sum((value - mean) ** 2 for value in differences) / (len(differences) - 1)
    std = math.sqrt(variance)
    if std == 0:
        return 0.0
    return mean / std
