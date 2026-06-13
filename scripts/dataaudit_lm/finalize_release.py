from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.io import write_csv, write_json, write_text
from dataaudit_lm.integrity.paths import INTEGRITY, REPORTS, TABLES, ensure_public_artifact_dirs
from dataaudit_lm.registry.metadata import collect_evidence_summary, summary_as_dict


def main() -> None:
    ensure_public_artifact_dirs()
    summary = collect_evidence_summary()
    evidence = summary_as_dict(summary)
    status = "DATA_PIPELINE_VERIFIED"
    if summary.completed_runs > 0 and summary.tokens_per_run >= 5_000_000:
        status = "MULTI_SEED_TRAINING_COMPLETED"
    final_release = summary.final_gate_passed
    release = {
        "evidence": evidence,
        "final_release_gate_passed": final_release,
        "status": status,
        "unfinished_items": [] if final_release else [
            "Run matrix has not reached 2 datasets x 8 methods x 5 seeds.",
            "Official downstream task suite is not complete.",
            "Clean public naming migration is not complete.",
        ],
    }
    write_json(REPORTS / "final_release_report.json", release)
    lines = [
        "# DataAudit-LM Release Report",
        "",
        f"- Status: `{status}`",
        f"- Final release gate passed: `{final_release}`",
        f"- Datasets: `{summary.dataset_count}`",
        f"- Methods: `{summary.method_count}`",
        f"- Seeds: `{summary.seed_count}`",
        f"- Completed runs: `{summary.completed_runs}`",
        f"- Target runs: `{summary.target_runs}`",
        f"- Tokens per completed run: `{summary.tokens_per_run}`",
        f"- Aggregate tokens seen: `{summary.total_tokens_seen}`",
        "",
        "## Unfinished Items",
        "",
    ]
    lines.extend(f"- {item}" for item in release["unfinished_items"] or ["none"])
    write_text(REPORTS / "final_release_report.md", "\n".join(lines))
    write_csv(TABLES / "evidence_summary.csv", list(evidence), [evidence])
    write_json(INTEGRITY / "release_manifest.json", release)
    print(json.dumps({"status": status, "final_release_gate_passed": final_release}))


if __name__ == "__main__":
    main()
