from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_mechanism_outputs_failure_taxonomy() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_v2_mechanism_report.json").read_text(encoding="utf-8"))
    assert report["localmax_v2_mechanism_ready"] is True
    rows = list(csv.DictReader((ROOT / "artifacts/localmax_v2_analysis/failure_taxonomy.csv").open(encoding="utf-8")))
    assert len(rows) >= 1
    assert any(row["failure_type"] == "urd_claim_not_supported" for row in rows)
