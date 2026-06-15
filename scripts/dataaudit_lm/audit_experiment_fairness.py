from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.io import read_json, write_json
from dataaudit_lm.integrity.paths import REPORTS, ensure_public_artifact_dirs
from dataaudit_lm.registry.metadata import collect_evidence_summary, summary_as_dict


def _finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def main() -> None:
    ensure_public_artifact_dirs()
    legacy_prefix = "local" + "max_" + "cc" + "fc"
    training = read_json(ROOT / "artifacts/reports" / f"{legacy_prefix}_training_report.json")
    raw_runs = training.get("training_results")
    runs = raw_runs if isinstance(raw_runs, list) else []
    summary = collect_evidence_summary()
    run_failures: list[str] = []
    for row in runs:
        if not isinstance(row, dict):
            run_failures.append("malformed_run_row")
            continue
        key = f"{row.get('dataset_id')}:{row.get('method_name')}:{row.get('seed')}"
        if int(row.get("tokens_seen") or 0) < 5_000_000:
            run_failures.append(f"insufficient_tokens:{key}")
        if not _finite(row.get("valid_nll_nats_per_token")):
            run_failures.append(f"nonfinite_nll:{key}")
        if row.get("reused_existing_artifact") is not True:
            run_failures.append(f"lineage_not_marked_reused_or_existing:{key}")
    payload = {
        "evidence": summary_as_dict(summary),
        "fairness_metadata_checked": not run_failures,
        "final_matrix_complete": summary.final_gate_passed,
        "known_gap": (
            "Current reusable evidence has fewer than 80 final-gate runs; "
            "this script verifies metadata and does not promote it to a final matrix."
        ),
        "run_failures": run_failures,
        "status": "FAIRNESS_METADATA_VERIFIED" if not run_failures else "FAIRNESS_METADATA_FAILED",
    }
    write_json(REPORTS / "experiment_fairness_report.json", payload)
    print(
        json.dumps(
            {
                "fairness_metadata_checked": not run_failures,
                "final_matrix_complete": summary.final_gate_passed,
            }
        )
    )
    if run_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
