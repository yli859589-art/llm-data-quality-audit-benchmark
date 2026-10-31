from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_ccfc_training_matrix_is_complete_and_finite() -> None:
    report = json.loads(
        (ROOT / "artifacts/reports/localmax_ccfc_training_report.json").read_text(encoding="utf-8")
    )
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
    report = json.loads(
        (ROOT / "artifacts/reports/localmax_ccfc_readiness_report.json").read_text(encoding="utf-8")
    )
    assert report["ccfc_candidate_ready"] is True
    assert report["current_readiness"] == "TOP_TIER_CCFC_PROJECT_CANDIDATE"
    assert report["ccf_c_paper_claimed"] is False
    assert report["ccf_b_ready_claimed"] is False
    assert report["level3_completed_artifact"] is False
    assert report["completed_training_runs"] == 42


def test_ccfc_does_not_modify_historical_main_results() -> None:
    report = json.loads(
        (ROOT / "artifacts/reports/localmax_ccfc_readiness_report.json").read_text(encoding="utf-8")
    )
    assert report["historical_results_modified"] is False
    expected = {
        "artifacts/tables/main_results.csv": "D8E593744EEB95CECB422C600CEC89C70279B28E09FCD3DE96AA8D1C9F2A7C3F",
        "artifacts/stats/main_results.csv": "38AA59CE82B2511FBF711D4B696E7B47C7C89F94D2ABCA0835D75AC0F14057B4",
        "artifacts/cross_dataset/cross_dataset_results.csv": "5003F1534231EEDAEE6B501D6F9769C45CEF749CFE37921E8AB10CCE12C73A86",
        "artifacts/runs/run_registry.jsonl": "D9EF6C857EC44CEF1659F1444752C6B4FC2C86C443F27665621CEA39B45086D8",
    }
    for path, digest in expected.items():
        actual = (
            hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest().upper()
        )
        assert actual == digest
