from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_statistics_block_unsupported_urd_claims() -> None:
    rows = list(csv.DictReader((ROOT / "artifacts/localmax_v2_tables/localmax_v2_statistical_tests.csv").open(encoding="utf-8")))
    urd_rows = [row for row in rows if row["comparison"] == "urd_fixed_vs_raw"]
    assert len(urd_rows) == 2
    assert all(row["improvement_claim_allowed"] == "False" for row in urd_rows)
    length_openweb = next(row for row in rows if row["dataset_id"] == "openwebtext_v2_100m" and row["comparison"] == "length_filter_vs_raw")
    assert length_openweb["improvement_claim_allowed"] == "True"
