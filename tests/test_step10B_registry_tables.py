from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10b_table_status_is_not_fake_main_results() -> None:
    status = json.loads((ROOT / "artifacts/level3_tables/step10B_table_generation_status.json").read_text(encoding="utf-8"))

    assert status["status"] == "not_generated"
    assert status["registry_backed"] is True
    assert status["new_level3_main_results_added"] is False
    assert not (ROOT / "artifacts/level3_tables/level3_main_results.csv").exists()


def test_step10b_reports_are_present_for_review() -> None:
    assert (ROOT / "artifacts/level3_reports/level3_limitations.md").exists()
    assert (ROOT / "artifacts/level3_reports/level3_reproducibility.md").exists()
    assert (ROOT / "artifacts/level3_reports/step10B_execution_summary.md").exists()

