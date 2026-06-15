from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


def test_dataaudit_rehearsal_runs_through_new_package_path() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dataaudit_lm/run_rehearsal.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "rehearsal_passed" in result.stdout
    report = json.loads(
        (ROOT / "artifacts/dataaudit_lm/reports/rehearsal_report.json").read_text(encoding="utf-8")
    )
    assert report["status"] == "passed"
    assert report["scope"] == "ENGINEERING_VALIDATION_ONLY"
    assert report["comparison_scope"] == "NOT_FOR_METHOD_COMPARISON"
    assert report["all_warm_start_false"] is True
    assert report["all_nll_finite"] is True
