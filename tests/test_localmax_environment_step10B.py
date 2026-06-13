from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_environment_report_has_resource_bounds() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_environment_report.json").read_text(encoding="utf-8"))

    assert report["step"] == "step10B_localmax_execution"
    assert report["recommended_token_budget_per_dataset"] == 50_000_000
    assert report["max_attempt_token_budget_per_dataset"] == 100_000_000
    assert report["recommended_main_model"] == "small_25m_40m"
    assert report["selected_model"] == "medium_lite_60m_80m"
    assert report["level3_completed_possible_on_this_machine"] is False
    assert report["level3_completed"] is False

