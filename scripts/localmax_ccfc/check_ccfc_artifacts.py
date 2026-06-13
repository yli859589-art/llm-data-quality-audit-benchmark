from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
LOCAL = SCRIPTS / "localmax_ccfc"
for path in [SCRIPTS, LOCAL]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ccfc_utils import protected_hashes_unchanged, read_csv, status_payload, write_report


EXPECTED_DATASETS = {"openwebtext_v2_100m", "c4_en_v2_100m"}
EXPECTED_METHODS = {
    "raw",
    "exact_dedup",
    "length_filter",
    "random_same_keep_rate",
    "c4_quality_filter",
    "perplexity_proxy_filter",
    "urd_fixed",
}
EXPECTED_SEEDS = {13, 42, 101}
EXPECTED_RUNS = len(EXPECTED_DATASETS) * len(EXPECTED_METHODS) * len(EXPECTED_SEEDS)
MIN_TOKENS_PER_RUN = 5_000_000


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _is_finite(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def _csv_has_nonfinite_literals(path: Path) -> bool:
    if not path.exists():
        return True
    lowered = path.read_text(encoding="utf-8").lower()
    return any(token in lowered for token in ["nan", "inf", "-inf", "infinity"])


def _training_checks(training_report: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    results = training_report.get("training_results")
    if not isinstance(results, list):
        return ["training_results_missing"]
    keys: set[tuple[str, str, int]] = set()
    for row in results:
        if not isinstance(row, dict):
            failures.append("malformed_training_result")
            continue
        dataset_id = str(row.get("dataset_id"))
        method_name = str(row.get("method_name"))
        try:
            seed = int(row.get("seed"))
        except (TypeError, ValueError):
            failures.append(f"invalid_seed:{dataset_id}:{method_name}")
            continue
        keys.add((dataset_id, method_name, seed))
        if dataset_id not in EXPECTED_DATASETS:
            failures.append(f"unexpected_dataset:{dataset_id}")
        if method_name not in EXPECTED_METHODS:
            failures.append(f"unexpected_method:{method_name}")
        if seed not in EXPECTED_SEEDS:
            failures.append(f"unexpected_seed:{seed}")
        if not row.get("completed"):
            failures.append(f"incomplete_run:{dataset_id}:{method_name}:{seed}")
        if int(row.get("tokens_seen") or 0) < MIN_TOKENS_PER_RUN:
            failures.append(f"insufficient_tokens:{dataset_id}:{method_name}:{seed}")
        for metric in ["valid_nll_nats_per_token", "valid_log_ppl", "valid_ppl"]:
            if not _is_finite(row.get(metric)):
                failures.append(f"nonfinite_{metric}:{dataset_id}:{method_name}:{seed}")
    expected_keys = {
        (dataset_id, method_name, seed)
        for dataset_id in EXPECTED_DATASETS
        for method_name in EXPECTED_METHODS
        for seed in EXPECTED_SEEDS
    }
    missing = sorted(expected_keys - keys)
    if missing:
        failures.extend(f"missing_run:{dataset}:{method}:{seed}" for dataset, method, seed in missing)
    if len(results) != EXPECTED_RUNS:
        failures.append(f"unexpected_training_result_count:{len(results)}")
    if training_report.get("completed_core_runs") != EXPECTED_RUNS:
        failures.append("completed_core_runs_not_42")
    if training_report.get("expected_core_runs") != EXPECTED_RUNS:
        failures.append("expected_core_runs_not_42")
    if int(training_report.get("min_tokens_seen_per_completed_run") or 0) < MIN_TOKENS_PER_RUN:
        failures.append("min_tokens_seen_below_threshold")
    if not training_report.get("ccfc_training_ready"):
        failures.append("ccfc_training_ready_false")
    return failures


def _table_checks(root: Path) -> list[str]:
    failures: list[str] = []
    required_tables = [
        root / "artifacts/localmax_ccfc_tables/ccfc_main_results.csv",
        root / "artifacts/localmax_ccfc_tables/ccfc_method_summary.csv",
        root / "artifacts/localmax_ccfc_tables/ccfc_statistical_tests.csv",
        root / "artifacts/localmax_ccfc_tables/ccfc_risk_diversity_cost.csv",
        root / "artifacts/localmax_ccfc_downstream/downstream_subset.csv",
    ]
    for path in required_tables:
        if not path.exists():
            failures.append(f"missing_table:{path.relative_to(root).as_posix()}")
            continue
        rows = read_csv(path)
        if not rows:
            failures.append(f"empty_table:{path.relative_to(root).as_posix()}")
        if _csv_has_nonfinite_literals(path):
            failures.append(f"nonfinite_literal_in_table:{path.relative_to(root).as_posix()}")

    main_rows = read_csv(root / "artifacts/localmax_ccfc_tables/ccfc_main_results.csv")
    if len(main_rows) != EXPECTED_RUNS:
        failures.append(f"main_results_row_count_not_42:{len(main_rows)}")
    datasets = {row.get("dataset_id") for row in main_rows}
    methods = {row.get("method_name") for row in main_rows}
    seeds = {int(row.get("seed") or -1) for row in main_rows}
    if datasets != EXPECTED_DATASETS:
        failures.append("main_results_dataset_set_mismatch")
    if methods != EXPECTED_METHODS:
        failures.append("main_results_method_set_mismatch")
    if seeds != EXPECTED_SEEDS:
        failures.append("main_results_seed_set_mismatch")
    return failures


def main() -> None:
    report_dir = ROOT / "artifacts/reports"
    training_report = _load_json(report_dir / "localmax_ccfc_training_report.json")
    filter_report = _load_json(report_dir / "localmax_ccfc_filter_report.json")
    evaluation_report = _load_json(report_dir / "localmax_ccfc_evaluation_report.json")
    downstream_report = _load_json(report_dir / "localmax_ccfc_downstream_report.json")
    readiness_report = _load_json(report_dir / "localmax_ccfc_readiness_report.json")

    failures: list[str] = []
    failures.extend(_training_checks(training_report))
    failures.extend(_table_checks(ROOT))
    if not filter_report.get("ccfc_filters_ready"):
        failures.append("ccfc_filters_ready_false")
    filter_results = filter_report.get("filter_results")
    if not isinstance(filter_results, list) or len(filter_results) != 14:
        failures.append("completed_filter_runs_not_14")
    if not evaluation_report.get("ccfc_evaluation_ready"):
        failures.append("ccfc_evaluation_ready_false")
    if evaluation_report.get("lm_metric_rows") != EXPECTED_RUNS:
        failures.append("evaluation_lm_metric_rows_not_42")
    if not downstream_report.get("downstream_completed"):
        failures.append("downstream_completed_false")
    if int(downstream_report.get("completed_rows") or 0) < 8:
        failures.append("downstream_completed_rows_below_expected")
    if downstream_report.get("official_full_downstream") is not False:
        failures.append("downstream_scope_not_marked_local")
    if not readiness_report.get("ccfc_candidate_ready"):
        failures.append("ccfc_candidate_ready_false")
    if readiness_report.get("ccf_c_paper_claimed") is not False:
        failures.append("ccf_c_paper_claimed_true")
    if readiness_report.get("ccf_b_ready_claimed") is not False:
        failures.append("ccf_b_ready_claimed_true")
    if not protected_hashes_unchanged():
        failures.append("protected_historical_result_hash_changed")

    ready = not failures
    payload = status_payload(
        "artifact_check",
        ready,
        failures,
        {
            "current_readiness": "CCFC_ARTIFACTS_CHECKED" if ready else "CCFC_ARTIFACTS_BLOCKED",
            "ccfc_artifact_check_passed": ready,
            "expected_training_runs": EXPECTED_RUNS,
            "expected_filter_runs": 14,
            "min_tokens_per_run": MIN_TOKENS_PER_RUN,
            "checked_reports": [
                "artifacts/reports/localmax_ccfc_filter_report.json",
                "artifacts/reports/localmax_ccfc_training_report.json",
                "artifacts/reports/localmax_ccfc_evaluation_report.json",
                "artifacts/reports/localmax_ccfc_downstream_report.json",
                "artifacts/reports/localmax_ccfc_readiness_report.json",
            ],
        },
    )
    write_report(payload, "localmax_ccfc_artifact_check_report", "LocalMax CCFC Artifact Check")
    print(
        json.dumps(
            {
                "ccfc_artifact_check_passed": ready,
                "expected_training_runs": EXPECTED_RUNS,
                "blocking_failures": failures,
            },
            sort_keys=True,
        )
    )
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
