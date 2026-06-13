from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from localmax_v2_utils import (
    ROOT,
    V2_TABLES,
    load_json,
    protected_hashes,
    protected_hashes_unchanged,
    read_csv,
    status_payload,
    write_csv,
    write_report,
)


def _copy_csv(source: Path, target: Path) -> int:
    rows = read_csv(source)
    write_csv(target, list(rows[0].keys()) if rows else ["empty"], rows)
    return len(rows)


def _data_summary() -> list[dict[str, Any]]:
    report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_data_report.json")
    return [
        {
            "dataset_id": row["dataset_id"],
            "dataset_name": row["dataset_name"],
            "actual_gpt2_tokens": row["actual_gpt2_tokens"],
            "raw_bytes": row["raw_bytes"],
            "compressed_bytes": row["compressed_bytes"],
            "document_count": row["document_count"],
            "fallback_used": row["fallback_used"],
            "no_fallback_verified": row["no_fallback_verified"],
            "duplicate_rate": row.get("duplicate_rate", 0.0),
            "data_manifest": row["data_manifest_path"],
            "evidence_level": "localmax_v2_data",
        }
        for row in report.get("datasets", [])
    ]


def _training_summary() -> list[dict[str, Any]]:
    report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_training_report.json")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in report.get("training_results", []):
        if row.get("completed") is True:
            grouped[(row["dataset_id"], row["method_name"])].append(row)
    rows = []
    for (dataset_id, method), group in sorted(grouped.items()):
        rows.append(
            {
                "dataset_id": dataset_id,
                "method_name": method,
                "completed_runs": len(group),
                "model_scale": "small",
                "parameter_count": report.get("parameter_count", ""),
                "min_steps_completed": min(int(row["steps_completed"]) for row in group),
                "min_tokens_seen": min(int(row["tokens_seen"]) for row in group),
                "total_tokens_seen": sum(int(row["tokens_seen"]) for row in group),
                "context_length": report.get("context_length", 256),
                "metric_audit_passed": report.get("metric_audit_passed", False),
                "evidence_level": "localmax_v2_training_1m_tokens",
            }
        )
    return rows


def _main_results() -> list[dict[str, Any]]:
    lm_rows = read_csv(ROOT / "artifacts" / "localmax_v2_evaluation" / "lm_metrics.csv")
    rows = []
    for row in lm_rows:
        rows.append(
            {
                "dataset_id": row["dataset_id"],
                "method_name": row["method_name"],
                "seed": row["seed"],
                "model_scale": row["model_scale"],
                "steps_completed": row["steps_completed"],
                "tokens_seen": row["tokens_seen"],
                "valid_nll_nats_per_token": row["valid_nll_nats_per_token"],
                "valid_loss": row["valid_loss"],
                "valid_log_ppl": row["valid_log_ppl"],
                "valid_ppl": row["valid_ppl"],
                "ppl_overflow": row["ppl_overflow"],
                "metric_for_comparison": row["metric_for_comparison"],
                "training_manifest": row["training_manifest_path"],
                "evaluation_manifest": "artifacts/localmax_v2_evaluation/evaluation_manifest.json",
                "evidence_level": "localmax_v2_training_1m_tokens",
            }
        )
    return rows


def main() -> None:
    data_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_data_report.json")
    filter_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_filter_report.json")
    training_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_training_report.json")
    evaluation_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_evaluation_report.json")
    mechanism_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_mechanism_report.json")
    metric_audit = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_metric_audit.json")
    blocking: list[str] = []
    if data_report.get("datasets_meeting_100m_floor") != 2:
        blocking.append("Data gate failed: two datasets did not reach >=100M GPT-2 tokens.")
    if filter_report.get("localmax_v2_filters_ready") is not True:
        blocking.append("Filter gate failed.")
    if training_report.get("completed_core_runs") != 24:
        blocking.append("Training gate failed: 24 core runs not completed.")
    if int(training_report.get("min_tokens_seen_per_completed_run", 0)) < 1_000_000:
        blocking.append("Training gate failed: at least one core run is below 1M tokens_seen.")
    if metric_audit.get("metric_audit_passed") is not True:
        blocking.append("Metric audit gate failed.")
    if evaluation_report.get("localmax_v2_evaluation_ready") is not True:
        blocking.append("Evaluation gate failed.")
    if mechanism_report.get("localmax_v2_mechanism_ready") is not True:
        blocking.append("Mechanism gate failed.")
    if not protected_hashes_unchanged():
        blocking.append("Protected historical result hash changed.")
    main_rows = _main_results()
    if not main_rows:
        blocking.append("Main V2 result table would be empty.")
    V2_TABLES.mkdir(parents=True, exist_ok=True)
    write_csv(V2_TABLES / "localmax_v2_main_results.csv", list(main_rows[0].keys()) if main_rows else ["empty"], main_rows)
    data_rows = _data_summary()
    write_csv(V2_TABLES / "localmax_v2_dataset_summary.csv", list(data_rows[0].keys()) if data_rows else ["empty"], data_rows)
    training_rows = _training_summary()
    write_csv(V2_TABLES / "localmax_v2_training_summary.csv", list(training_rows[0].keys()) if training_rows else ["empty"], training_rows)
    for src, dest in [
        ("method_summary.csv", "localmax_v2_method_summary.csv"),
        ("statistical_tests.csv", "localmax_v2_statistical_tests.csv"),
        ("risk_diversity_cost.csv", "localmax_v2_risk_diversity_cost.csv"),
        ("pareto_results.csv", "localmax_v2_pareto_results.csv"),
    ]:
        _copy_csv(ROOT / "artifacts" / "localmax_v2_evaluation" / src, V2_TABLES / dest)
    _copy_csv(ROOT / "artifacts" / "localmax_v2_analysis" / "failure_taxonomy.csv", V2_TABLES / "localmax_v2_mechanism_results.csv")
    _copy_csv(ROOT / "artifacts" / "localmax_v2_downstream" / "downstream_subset.csv", V2_TABLES / "localmax_v2_downstream_subset.csv")
    ready = not blocking
    report = status_payload(
        "readiness",
        ready,
        blocking,
        {
            "status": "completed" if ready else "completed_with_failures",
            "current_readiness": "LOCAL_MAX_V2_STRONG_EVIDENCE_COMPLETED" if ready else "LOCAL_MAX_V2_PARTIAL_WITH_REAL_EVIDENCE",
            "localmax_v2_core_gates_passed": ready,
            "datasets_meeting_100m_floor": data_report.get("datasets_meeting_100m_floor"),
            "total_actual_gpt2_tokens": data_report.get("total_actual_gpt2_tokens"),
            "filter_matrix_completed": filter_report.get("localmax_v2_filters_ready"),
            "completed_core_runs": training_report.get("completed_core_runs"),
            "expected_core_runs": training_report.get("expected_core_runs"),
            "min_tokens_seen_per_completed_run": training_report.get("min_tokens_seen_per_completed_run"),
            "total_training_tokens_seen": training_report.get("total_training_tokens_seen"),
            "metric_audit_passed": metric_audit.get("metric_audit_passed"),
            "evaluation_completed": evaluation_report.get("localmax_v2_evaluation_ready"),
            "mechanism_completed": mechanism_report.get("localmax_v2_mechanism_ready"),
            "official_downstream_completed": False,
            "main_table_rows": len(main_rows),
            "historical_results_modified": not protected_hashes_unchanged(),
            "protected_hashes": protected_hashes(),
            "recommended_next_step": "finalize_localmax_v2_release" if ready else "fix_blocking_gates_before_release",
        },
    )
    write_report(report, "localmax_v2_readiness_report", "LocalMax V2 Readiness Report")
    print(json.dumps({"localmax_v2_core_gates_passed": ready, "current_readiness": report["current_readiness"], "main_rows": len(main_rows)}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
