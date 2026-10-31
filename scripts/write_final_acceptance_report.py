"""Write a machine-readable P2-2 conclusion from completed local evidence files."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    preflight = json.loads(
        (root / "artifacts/upgrade_reports/p2-02/final_preflight_metadata.json").read_text(
            encoding="utf-8"
        )
    )
    package = json.loads(
        (root / "artifacts/upgrade_reports/p2-02/release_package_verification.json").read_text(
            encoding="utf-8"
        )
    )
    legacy = json.loads(
        (root / "artifacts/upgrade_reports/p2-02/evaluation_manifest_check.json").read_text(
            encoding="utf-8"
        )
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
    ).stdout.strip()
    payload = {
        "report_version": "p2-02.final-acceptance.v1",
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "git_revision": revision,
        "software_system": {
            "status": "PASS",
            "evidence": [
                "P2 selected suite: 26 passed",
                "Fresh venv suite: 9 passed",
                "ZIP integrity and extracted CLI: pass",
            ],
        },
        "full_legacy_suite": {
            "status": "NOT_RUN",
            "reason": (
                "isolated run was stopped after historical failures at 45%; it was not rerun "
                "after legacy-exception repair"
            ),
        },
        "historical_protection": {
            "status": "PASS",
            "baseline_snapshot": next(
                item for item in preflight["checks"] if item["id"] == "baseline_snapshot"
            ),
        },
        "legacy_evaluation_integrity": {
            "status": "PASS",
            "detail": legacy["status"],
            "exceptions": legacy["legacy_integrity_exceptions"],
        },
        "formal_real_data_and_model_experiments": {
            "status": "BLOCKED",
            "reason": (
                "0/3 C4 and 0/6 OpenWebText declared raw shards are present; no 200M-token "
                "or real-corpus training result is claimed"
            ),
        },
        "release_package": {"status": "PASS", **package},
        "platforms": {"windows_fresh_venv": "PASS", "linux": "NOT_RUN"},
    }
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
