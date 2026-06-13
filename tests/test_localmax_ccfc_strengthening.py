from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_ccfc_training_matrix_is_complete_and_finite() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_ccfc_training_report.json").read_text(encoding="utf-8"))
    assert report["ccfc_training_ready"] is True
    assert report["completed_core_runs"] == 42
    assert report["expected_core_runs"] == 42
    assert report["target_tokens_seen_per_run"] == 5_000_000
    for row in report["training_results"]:
        assert row["completed"] is True
        assert int(row["tokens_seen"]) >= 5_000_000
        assert math.isfinite(float(row["valid_nll_nats_per_token"]))


def test_ccfc_result_tables_have_no_nonfinite_literals() -> None:
    for table in [
        "artifacts/localmax_ccfc_tables/ccfc_main_results.csv",
        "artifacts/localmax_ccfc_tables/ccfc_method_summary.csv",
        "artifacts/localmax_ccfc_tables/ccfc_statistical_tests.csv",
        "artifacts/localmax_ccfc_downstream/downstream_subset.csv",
    ]:
        rows = _rows(table)
        assert rows
        for row in rows:
            for value in row.values():
                assert value.strip().casefold() not in {"nan", "inf", "-inf"}


def test_ccfc_readiness_claim_boundary_is_honest() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_ccfc_readiness_report.json").read_text(encoding="utf-8"))
    assert report["ccfc_candidate_ready"] is True
    assert report["current_readiness"] == "TOP_TIER_CCFC_PROJECT_CANDIDATE"
    assert report["ccf_c_paper_claimed"] is False
    assert report["ccf_b_ready_claimed"] is False
    assert report["level3_completed_artifact"] is False
    assert report["completed_training_runs"] == 42


def test_ccfc_does_not_modify_historical_main_results() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_ccfc_readiness_report.json").read_text(encoding="utf-8"))
    assert report["historical_results_modified"] is False
    protected = report["protected_hashes"]
    assert protected["artifacts/tables/main_results.csv"] == "EAB3478D19E04CAF97E07FC31FCD3CC36089C19320A64E96F7BAC9EB12D89921"
    assert protected["artifacts/stats/main_results.csv"] == "E40944BB6476D84E8C3FC65670B2DC5E7DB62CF47CA7FC6D0051768458CD0E32"
    assert protected["artifacts/cross_dataset/cross_dataset_results.csv"] == "8DA3E015146193FCD5D1F5F47A9E0A5ED84F55A4182B4BB5932DC657B8DAAD4C"
    assert protected["artifacts/runs/run_registry.jsonl"] == "A05A06FCA305CEDF2C46DBEAD17AC222A5F09E73AB105538479A049DF90A26CE"
