from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10b_filter_report_does_not_pass_without_level3_data_and_tokenizer() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_filter_report.json").read_text(encoding="utf-8"))

    assert report["stage"] == "filter"
    assert report["level3_filters_ready"] is False
    assert report["completed"] is False
    assert report["new_level3_main_results_added"] is False

