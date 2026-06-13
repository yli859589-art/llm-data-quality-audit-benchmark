from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_readiness_core_gates_passed() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_v2_readiness_report.json").read_text(encoding="utf-8"))
    assert report["localmax_v2_core_gates_passed"] is True
    assert report["current_readiness"] == "LOCAL_MAX_V2_STRONG_EVIDENCE_COMPLETED"
    assert report["datasets_meeting_100m_floor"] == 2
    assert report["completed_core_runs"] == 24
    assert report["min_tokens_seen_per_completed_run"] >= 1_000_000
    assert report["historical_results_modified"] is False
