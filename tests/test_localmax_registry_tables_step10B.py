from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_tables_have_manifest_backed_result_rows() -> None:
    status = json.loads((ROOT / "artifacts/localmax_tables/localmax_table_generation_status.json").read_text(encoding="utf-8"))

    assert status["result_rows_written"] > 0
    assert status["no_fake_metric_values_written"] is True
    for table in status["tables"]:
        path = ROOT / table["path"]
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == table["rows"]
    main_rows = list(csv.DictReader((ROOT / "artifacts/localmax_tables/localmax_main_results.csv").open(encoding="utf-8")))
    assert main_rows
    for row in main_rows:
        assert row["evidence_level"] in {"localmax_training_minimal", "localmax_training_strengthened"}
        manifest_path = row.get("training_manifest") or row.get("source_manifest_path")
        assert (ROOT / manifest_path).exists()


def test_localmax_artifacts_are_registry_scannable() -> None:
    registry = ROOT / "artifacts/registry_v2/artifact_registry.jsonl"
    assert registry.exists()
    rows = [json.loads(line) for line in registry.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert any(row["path"] == "artifacts/reports/step10B_localmax_readiness_report.json" for row in rows)
    assert any(row["path"].startswith("artifacts/localmax_tables/") for row in rows)
