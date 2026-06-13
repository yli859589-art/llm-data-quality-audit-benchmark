from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10b_readiness_records_partial_or_blocked_state() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_readiness_report.json").read_text(encoding="utf-8"))

    assert report["step"] == "step10B_level3_heavy_execution"
    assert report["status"] in {"completed", "completed_partial", "completed_with_failures"}
    assert report["environment_checked"] is True
    assert report["current_readiness"] == "LEVEL3_PIPELINE_READY"
    assert report["level3_completed_artifact"] is False
    assert report["heavy_execution_completed"] is False
    assert report["recommended_next_step"] == "continue_step10B_heavy_execution"
    assert report["blocking_failures"]

