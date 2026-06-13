from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_filters_run_after_data_floor_is_met() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_filter_report.json").read_text(encoding="utf-8"))

    assert report["localmax_filters_ready"] is True
    assert len(report["filter_results"]) >= 8
    assert set(report["methods_completed"]) >= {"raw", "exact_dedup", "length_filter", "urd_fixed"}
    for row in report["filter_results"]:
        manifest = json.loads((ROOT / row["filter_manifest_path"]).read_text(encoding="utf-8"))
        assert manifest["completed"] is True
        assert manifest["level3_filter"] is False
