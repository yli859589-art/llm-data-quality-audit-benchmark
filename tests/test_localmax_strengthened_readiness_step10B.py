from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_strengthened_readiness_is_training_evidence_not_level3() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_localmax_readiness_report.json").read_text(encoding="utf-8"))

    assert report["current_readiness"] == "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_COMPLETED"
    assert report["localmax_training_strengthened_completed"] is True
    assert report["strengthened_training_runs_completed"] == 24
    assert report["min_tokens_seen_per_completed_run"] >= 25_000
    assert report["localmax_completed"] is False
    assert report["level3_completed_artifact"] is False
    assert report["true_medium_completed"] is False
    assert report["large_lite_completed"] is False
    assert report["official_downstream_completed"] is False

