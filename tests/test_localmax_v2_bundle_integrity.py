from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_release_bundle_integrity() -> None:
    report = json.loads((ROOT / "artifacts/localmax_v2_release/reports/release_bundle_integrity_report.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "artifacts/localmax_v2_release/localmax_v2_release_manifest.json").read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["release_bundle_links_valid"] is True
    assert manifest["bundle_scope"] == "standalone_metadata_bundle"
    assert manifest["raw_data_included"] is False
    assert manifest["binary_checkpoints_included"] is False
    assert (ROOT / "artifacts/localmax_v2_release/tables/localmax_v2_main_results.csv").exists()
    assert len(list((ROOT / "artifacts/localmax_v2_release/figures").glob("*.png"))) >= 10
