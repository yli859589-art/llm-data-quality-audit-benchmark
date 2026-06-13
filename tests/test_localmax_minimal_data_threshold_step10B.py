from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_minimal_data_threshold_is_met_but_not_level3() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_data_report.json").read_text(encoding="utf-8"))

    assert report["datasets_meeting_20m_floor"] >= 2
    assert report["localmax_data_ready"] is True
    assert report["level3_data_ready"] is False
    for dataset in report["nontrivial_datasets"][:2]:
        manifest = json.loads((ROOT / dataset["manifest_path"]).read_text(encoding="utf-8"))
        assert manifest["actual_gpt2_tokens"] >= 20_000_000
        assert manifest["fallback_used"] is False
        assert manifest["no_fallback_verified"] is True
        assert manifest["level3_data"] is False

