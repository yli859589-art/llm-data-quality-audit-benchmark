from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path.cwd()


def test_ppl_clipping_is_explicit_and_comparisons_use_valid_loss() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_evaluation_strengthened_report.json").read_text(encoding="utf-8"))
    rows = list(csv.DictReader((ROOT / "artifacts/localmax_evaluation_strengthened/lm_metrics.csv").open(encoding="utf-8")))

    assert rows
    assert report["all_ppl_clipped"] is True
    assert report["ppl_comparable"] is False
    assert report["metric_for_comparison"] == "valid_loss"
    assert all(row["metric_for_comparison"] == "valid_loss" for row in rows)
    assert all(row["ppl_clipped"] == "True" for row in rows)
    assert all(row["ppl_comparable"] == "False" for row in rows)


def test_clipped_ppl_is_not_used_for_improvement_claims() -> None:
    stats = list(csv.DictReader((ROOT / "artifacts/localmax_evaluation_strengthened/statistical_tests.csv").open(encoding="utf-8")))

    assert stats
    assert all(row["metric_for_comparison"] == "valid_loss" for row in stats)
    assert not any(row["improvement_claim_allowed"] == "True" for row in stats if row["ci_crosses_zero"] == "True")

