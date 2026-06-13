from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_tables_are_non_empty_and_registry_backed() -> None:
    main = list(csv.DictReader((ROOT / "artifacts/localmax_v2_tables/localmax_v2_main_results.csv").open(encoding="utf-8")))
    assert len(main) == 24
    for row in main:
        assert row["evidence_level"] == "localmax_v2_training_1m_tokens"
        assert (ROOT / row["training_manifest"]).exists()
        assert (ROOT / row["evaluation_manifest"]).exists()
        assert row["metric_for_comparison"] == "valid_nll_nats_per_token"
