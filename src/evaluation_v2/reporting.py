from __future__ import annotations

from typing import Any


def simple_report(title: str, metrics: dict[str, Any], notes: str) -> str:
    lines = [
        f"# {title}",
        "",
        notes,
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]
    for key, value in metrics.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This Step 7 output is not main evidence and does not permit an effectiveness claim.",
        ]
    )
    return "\n".join(lines) + "\n"
