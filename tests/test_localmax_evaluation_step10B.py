from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_evaluation_runs_without_official_downstream_claim() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_evaluation_report.json").read_text(encoding="utf-8"))

    assert report["localmax_evaluation_ready"] is True
    assert report["aggregate_rows"] >= 8
    assert report["official_downstream_completed"] is False
    assert (ROOT / "artifacts/localmax_evaluation/lm_metrics.csv").exists()
    assert (ROOT / "artifacts/localmax_evaluation/statistical_tests.csv").exists()
