from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path.cwd()


def test_standalone_release_table_links_are_inside_bundle() -> None:
    rows = list(csv.DictReader((ROOT / "artifacts/localmax_release/tables/localmax_main_results_release.csv").open(encoding="utf-8")))

    assert len(rows) == 24
    for row in rows:
        for field in ["training_manifest", "evaluation_manifest"]:
            link = row[field]
            assert link.startswith("artifacts/localmax_release/")
            assert (ROOT / link).exists(), link


def test_release_bundle_integrity_report_passes() -> None:
    report = json.loads((ROOT / "artifacts/localmax_release/reports/release_bundle_integrity_report.json").read_text(encoding="utf-8"))

    assert report["status"] == "passed"
    assert report["bundle_scope"] == "standalone_metadata_bundle"
    assert report["release_bundle_links_valid"] is True
    assert report["raw_data_included"] is False
    assert report["binary_checkpoints_included"] is False
    assert report["copied_training_manifest_count"] == 24
    assert report["copied_metrics_count"] == 24
    assert report["copied_filter_manifest_count"] >= 8
    assert not report["dangling_links"]

