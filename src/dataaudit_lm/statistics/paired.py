from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PairedDifferences:
    differences: list[float]
    mean_difference: float
    wins: int
    ties: int
    losses: int


def paired_differences(candidate: list[float], reference: list[float]) -> PairedDifferences:
    if len(candidate) != len(reference) or not candidate:
        raise ValueError("candidate and reference must have the same non-zero length")
    diffs = [left - right for left, right in zip(candidate, reference, strict=True)]
    return PairedDifferences(
        differences=diffs,
        mean_difference=sum(diffs) / len(diffs),
        wins=sum(diff < 0 for diff in diffs),
        ties=sum(diff == 0 for diff in diffs),
        losses=sum(diff > 0 for diff in diffs),
    )
