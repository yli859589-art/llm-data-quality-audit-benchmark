from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10c_release_report_and_docs_exist() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10C_localmax_release_report.json").read_text(encoding="utf-8"))

    assert report["current_readiness"] == "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED"
    assert report["status"] == "completed"
    assert report["localmax_release_created"] is True
    assert report["level3_completed_artifact"] is False
    assert report["official_downstream_completed"] is False
    assert report["true_medium_completed"] is False
    assert report["large_lite_completed"] is False

    for rel in [
        "docs/LOCALMAX_RELEASE.md",
        "docs/LOCALMAX_RESULTS.md",
        "docs/LOCALMAX_LIMITATIONS.md",
        "docs/LOCALMAX_REPRODUCIBILITY.md",
        "docs/LOCALMAX_CLAIM_BOUNDARY.md",
        "docs/LOCALMAX_MODEL_CARD.md",
        "docs/LOCALMAX_DATA_CARD.md",
        "docs/LOCALMAX_FAILURE_ANALYSIS.md",
        "docs/LOCALMAX_FUTURE_CLOUD_LEVEL3.md",
    ]:
        assert (ROOT / rel).exists(), rel


def test_step10c_release_main_table_is_manifest_backed() -> None:
    table = ROOT / "artifacts/localmax_release/tables/localmax_main_results_release.csv"
    rows = list(csv.DictReader(table.open(encoding="utf-8", newline="")))

    assert len(rows) == 24
    for row in rows:
        assert row["metric_for_comparison"] == "valid_loss"
        assert float(row["valid_loss"]) > 0
        assert row["ppl_clipped"] == "True"
        assert row["ppl_comparable"] == "False"
        assert (ROOT / row["training_manifest"]).exists()
        assert (ROOT / row["evaluation_manifest"]).exists()

