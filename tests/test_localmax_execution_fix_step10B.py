from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_execution_fix_completed_minimal_real_evidence_without_step10c() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_localmax_readiness_report.json").read_text(encoding="utf-8"))

    assert report["current_readiness"] in {
        "LOCAL_MAX_MINIMAL_REAL_EVIDENCE_COMPLETED",
        "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_COMPLETED",
    }
    assert report["localmax_minimal_real_evidence_completed"] is True
    assert report["localmax_completed"] is False
    assert report["level3_completed_artifact"] is False
    assert "step10C" in report["recommended_next_step"]
