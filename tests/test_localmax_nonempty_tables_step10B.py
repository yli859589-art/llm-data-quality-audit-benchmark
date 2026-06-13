from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()


def test_nonempty_main_table_is_backed_by_training_manifests() -> None:
    table = ROOT / "artifacts/localmax_tables/localmax_main_results.csv"
    with table.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) >= 24
    for row in rows:
        assert row["metric_for_comparison"] == "valid_loss"
        assert float(row["valid_loss"]) > 0
        assert int(row["tokens_seen"]) >= 25_000
        assert int(row["steps_completed"]) >= 100
        assert (ROOT / row["training_manifest"]).exists()
