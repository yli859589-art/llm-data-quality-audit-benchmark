from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10b_mechanism_report_blocks_full_scale_claim() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10B_mechanism_report.json").read_text(encoding="utf-8"))

    assert report["level3_mechanism_ready"] is False
    assert report["completed"] is False
    assert report["level3_completed_artifact"] is False

