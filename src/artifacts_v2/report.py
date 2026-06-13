from __future__ import annotations

from pathlib import Path

from .canonical_io import write_canonical_text


def write_registry_report(root: Path, summary: dict) -> Path:
    path = root / "artifacts" / "reports" / "artifact_registry_v2_report.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Artifact Registry V2 Report",
        "",
        f"- Records: `{summary['record_count']}`",
        f"- Main evidence records: `{summary['main_evidence_records']}`",
        f"- Level 3 evidence records: `{summary['level3_evidence_records']}`",
        "",
        "## Artifact Types",
        "",
        "| Type | Count |",
        "|---|---:|",
    ]
    for key, value in summary["artifact_type_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Warnings", ""])
    for warning in summary.get("warnings", []):
        lines.append(f"- {warning}")
    return write_canonical_text(path, "\n".join(lines))
