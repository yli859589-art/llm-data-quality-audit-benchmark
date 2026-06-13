from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_evaluation_outputs_valid_nll_and_ppl() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_v2_evaluation_report.json").read_text(encoding="utf-8"))
    assert report["localmax_v2_evaluation_ready"] is True
    assert report["lm_metric_rows"] == 24
    assert report["metric_for_comparison"] == "valid_nll_nats_per_token"
    assert report["ppl_valid"] is True
    assert report["ppl_overflow_count"] == 0
    rows = list(csv.DictReader((ROOT / "artifacts/localmax_v2_evaluation/lm_metrics.csv").open(encoding="utf-8")))
    assert len(rows) == 24
    assert all(float(row["valid_ppl"]) > 1.0 for row in rows)
