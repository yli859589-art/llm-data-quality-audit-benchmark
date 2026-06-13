from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path.cwd()


def test_strengthened_main_results_schema_and_rows() -> None:
    rows = list(csv.DictReader((ROOT / "artifacts/localmax_tables/localmax_main_results.csv").open(encoding="utf-8")))

    assert len(rows) == 24
    required = {
        "dataset",
        "method",
        "seed",
        "model_scale",
        "steps_completed",
        "tokens_seen",
        "valid_loss",
        "valid_ppl_clipped",
        "ppl_clipped",
        "ppl_comparable",
        "metric_for_comparison",
        "training_manifest",
        "evaluation_manifest",
        "evidence_level",
    }
    assert required.issubset(rows[0])
    for row in rows:
        assert int(row["steps_completed"]) >= 100
        assert int(row["tokens_seen"]) >= 25_000
        assert row["evidence_level"] == "localmax_training_strengthened"
        assert (ROOT / row["training_manifest"]).exists()
        assert (ROOT / row["evaluation_manifest"]).exists()
