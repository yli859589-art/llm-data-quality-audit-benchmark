from __future__ import annotations

from typing import Any


OBJECTIVES = [
    "utility_score",
    "diversity_score",
    "risk_score",
    "shift_penalty",
    "cost_score",
]


def _dominates(left: dict[str, float], right: dict[str, float]) -> bool:
    left_values = [
        left["utility_score"],
        left["diversity_score"],
        1.0 - left["risk_score"],
        1.0 - left["shift_penalty"],
        1.0 - left["cost_score"],
    ]
    right_values = [
        right["utility_score"],
        right["diversity_score"],
        1.0 - right["risk_score"],
        1.0 - right["shift_penalty"],
        1.0 - right["cost_score"],
    ]
    return all(a >= b for a, b in zip(left_values, right_values)) and any(
        a > b for a, b in zip(left_values, right_values)
    )


def pareto_layers(rows: list[dict[str, Any]]) -> dict[str, Any]:
    remaining = set(range(len(rows)))
    ranks = [0 for _ in rows]
    layers: list[list[str]] = []
    rank = 0
    while remaining:
        frontier = []
        for index in sorted(remaining):
            if not any(_dominates(rows[other], rows[index]) for other in remaining if other != index):
                frontier.append(index)
        if not frontier:
            frontier = [min(remaining)]
        for index in frontier:
            ranks[index] = rank
            remaining.remove(index)
        layers.append([str(rows[index]["doc_id"]) for index in frontier])
        rank += 1
    return {
        "objectives": [
            "maximize utility_score",
            "maximize diversity_score",
            "minimize risk_score",
            "minimize shift_penalty",
            "minimize cost_score",
        ],
        "ranks": {str(rows[index]["doc_id"]): ranks[index] for index in range(len(rows))},
        "layers": layers,
        "notes": "Transparent non-dominated sorting for Step 6 smoke selection.",
    }
