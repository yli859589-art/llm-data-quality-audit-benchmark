from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_mechanism_runs_but_no_full_scale_claim() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_mechanism_report.json").read_text(encoding="utf-8"))

    assert report["localmax_mechanism_ready"] is True
    assert report["full_scale_mechanism_claim_allowed"] is False
    assert (ROOT / "artifacts/localmax_analysis/negative_result_analysis.md").exists()
