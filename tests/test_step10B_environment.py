from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def _report(name: str) -> dict:
    return json.loads((ROOT / "artifacts/reports" / name).read_text(encoding="utf-8"))


def test_step10b_environment_report_exists_and_is_truthful() -> None:
    report = _report("step10B_environment_report.json")

    assert report["step"] == "step10B_level3_heavy_execution"
    assert report["stage"] == "environment"
    assert report["heavy_execution_feasible"] in {True, False}
    assert isinstance(report["disk_free_gb"], (int, float))
    assert report["expected_storage_estimate_gb"] >= 500
    if report["heavy_execution_feasible"] is False:
        assert report["blocking_failures"]
        assert report["heavy_execution_completed"] is False
        assert report["level3_completed_artifact"] is False

