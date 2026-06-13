from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_readiness_is_partial_and_honest() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_localmax_readiness_report.json").read_text(encoding="utf-8"))

    assert report["step"] == "step10B_localmax_execution_fix"
    assert report["current_readiness"] in {
        "LOCAL_MAX_MINIMAL_REAL_EVIDENCE_COMPLETED",
        "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_COMPLETED",
    }
    assert report["localmax_minimal_real_evidence_completed"] is True
    assert report["localmax_completed"] is False
    assert report["partial_real_evidence"] is True
    assert report["level3_completed"] is False
    assert report["true_medium_completed"] is False
    assert report["large_lite_completed"] is False
    assert report["recommended_next_step"] in {
        "step10B_localmax_expand_methods_or_step10C_after_review",
        "external_review_before_step10C",
    }
