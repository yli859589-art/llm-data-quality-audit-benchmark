from __future__ import annotations

from typing import Any


def mechanism_report(title: str, summary: dict[str, Any], notes: str) -> str:
    lines = [
        f"# {title}",
        "",
        notes,
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|---|---|",
    ]
    for key, value in summary.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This Step 8 artifact is smoke/protocol mechanism analysis. It is not main evidence, "
            "does not prove method effectiveness, and does not permit a full-scale mechanism conclusion.",
        ]
    )
    return "\n".join(lines) + "\n"

