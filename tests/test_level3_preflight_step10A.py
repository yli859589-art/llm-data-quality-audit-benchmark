from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()


def test_level3_protocol_and_preflight_scripts_pass_without_heavy_execution() -> None:
    subprocess.run(
        [sys.executable, "scripts/check_level3_protocol.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    subprocess.run(
        [sys.executable, "scripts/check_level3_preflight.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )

    protocol = json.loads((ROOT / "artifacts/reports/level3_protocol_check_report.json").read_text(encoding="utf-8"))
    preflight = json.loads((ROOT / "artifacts/reports/level3_preflight_report.json").read_text(encoding="utf-8"))

    assert protocol["status"] == "passed"
    assert protocol["protocol_only"] is True
    assert protocol["completed"] is False
    assert preflight["status"] == "passed"
    assert preflight["level3_completed_artifact"] is False
    assert preflight["heavy_execution_completed"] is False
    assert preflight["heavy_execution_ready"] is False
    assert preflight["current_readiness"] == "LEVEL3_PIPELINE_READY"


def test_step10A_readiness_report_preserves_pipeline_boundary() -> None:
    subprocess.run(
        [sys.executable, "scripts/write_step10A_readiness_report.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    report = json.loads((ROOT / "artifacts/reports/step10A_readiness_report.json").read_text(encoding="utf-8"))

    assert report["status"] == "completed"
    assert report["current_readiness"] == "LEVEL3_PIPELINE_READY"
    assert report["level3_completed_artifact"] is False
    assert report["heavy_protocol_frozen"] is True
    assert report["heavy_execution_completed"] is False
    assert report["main_results_modified"] is False
    assert report["new_experiments_added"] is False

