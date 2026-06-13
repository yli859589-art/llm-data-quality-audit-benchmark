from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10b_evaluation_report_blocks_official_downstream_claim() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_evaluation_report.json").read_text(encoding="utf-8"))

    assert report["level3_evaluation_ready"] is False
    assert report["level3_downstream_ready"] is False
    assert report["official_downstream_completed"] is False
    assert report["completed"] is False

