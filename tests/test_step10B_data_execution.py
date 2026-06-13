from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10b_data_report_does_not_pass_without_500m_data() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_data_report.json").read_text(encoding="utf-8"))

    assert report["stage"] == "data"
    assert report["level3_data_ready"] is False
    assert report["completed"] is False
    assert report["level3_completed_artifact"] is False
    assert report["new_level3_main_results_added"] is False

