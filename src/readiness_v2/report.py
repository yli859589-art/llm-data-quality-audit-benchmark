from __future__ import annotations

from pathlib import Path
from typing import Any

from artifacts_v2.canonical_io import write_canonical_json, write_canonical_text


def write_level3_gate_reports(root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    output_dir = root / "artifacts" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "level3_gates_report.json"
    md_path = output_dir / "level3_gates_report.md"
    write_canonical_json(json_path, report)
    lines = [
        "# Level 3 Gates Report",
        "",
        f"- Current readiness: `{report['current_readiness']}`",
        f"- Level 3 completed artifact: `{report['level3_completed_artifact']}`",
        f"- Heavy execution completed: `{report['heavy_execution_completed']}`",
        "",
        "| Gate | Status | Passed | Summary |",
        "|---|---|---:|---|",
    ]
    for name, gate in report["gates"].items():
        lines.append(f"| `{name}` | `{gate['status']}` | `{gate['passed']}` | {gate['summary']} |")
    write_canonical_text(md_path, "\n".join(lines))
    return json_path, md_path
