from __future__ import annotations

import json
import csv
from pathlib import Path

from localmax_utils import (
    LOCALMAX_REPORTS,
    LOCALMAX_TABLES,
    REPORTS,
    load_json,
    protected_hashes,
    protected_hashes_unchanged,
    status_payload,
    utc_now,
    write_csv,
    write_json,
    write_markdown,
    write_report,
)


TABLES = {
    "localmax_main_results.csv": [
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
    ],
    "localmax_baseline_results.csv": ["dataset_id", "baseline", "model_scale", "seed", "metric_name", "metric_value", "source_manifest_path"],
    "localmax_urd_ablation_results.csv": ["dataset_id", "ablation", "model_scale", "seed", "metric_name", "metric_value", "source_manifest_path"],
    "localmax_downstream_subset_results.csv": ["dataset_id", "task", "method", "metric_name", "metric_value", "source_manifest_path"],
    "localmax_risk_diversity_cost_results.csv": ["dataset_id", "method", "risk_metric", "diversity_metric", "cost_metric", "source_manifest_path"],
    "localmax_pareto_results.csv": ["dataset_id", "method", "utility", "risk", "cost", "pareto_status", "source_manifest_path"],
    "localmax_mechanism_results.csv": ["dataset_id", "method", "analysis_name", "finding", "source_manifest_path"],
    "localmax_statistical_tests.csv": ["dataset_id", "comparison", "test_name", "n_seeds", "ci_low", "ci_high", "significant", "source_manifest_path"],
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    return __import__("hashlib").sha256(path.read_bytes()).hexdigest().upper()


def main() -> None:
    report_names = {
        "environment": "localmax_environment_report.json",
        "data": "localmax_data_report.json",
        "tokenizer": "localmax_tokenizer_report.json",
        "filter": "localmax_filter_report.json",
        "small_training": "localmax_small_training_report.json",
        "medium_lite_training": "localmax_medium_lite_training_report.json",
        "evaluation": "localmax_evaluation_report.json",
        "mechanism": "localmax_mechanism_report.json",
    }
    reports = {name: load_json(REPORTS / filename) for name, filename in report_names.items()}
    strengthened_training = load_json(REPORTS / "localmax_training_strengthened_report.json")
    strengthened_evaluation = load_json(REPORTS / "localmax_evaluation_strengthened_report.json")
    strengthened_mechanism = load_json(REPORTS / "localmax_mechanism_strengthened_report.json")
    env_checked = bool(reports["environment"])
    data_ready = reports["data"].get("localmax_data_ready") is True
    tokenizer_ready = reports["tokenizer"].get("localmax_tokenizer_ready") is True
    filters_ready = reports["filter"].get("localmax_filters_ready") is True
    small_ready = reports["small_training"].get("localmax_small_training_ready") is True
    medium_lite_ready = reports["medium_lite_training"].get("localmax_medium_lite_training_ready") is True
    evaluation_ready = reports["evaluation"].get("localmax_evaluation_ready") is True
    mechanism_ready = reports["mechanism"].get("localmax_mechanism_ready") is True
    minimal_completed = all([env_checked, data_ready, tokenizer_ready, filters_ready, small_ready, evaluation_ready, mechanism_ready])
    strengthened_runs_completed = int(strengthened_training.get("completed_strengthened_runs", 0) or 0)
    strengthened_completed = (
        strengthened_training.get("training_strengthened_completed") is True
        and strengthened_evaluation.get("localmax_evaluation_strengthened_ready") is True
        and strengthened_mechanism.get("localmax_mechanism_strengthened_ready") is True
    )
    strengthened_partial = 16 <= strengthened_runs_completed < 24
    partial_real = bool(reports["data"].get("partial_real_data_evidence")) or bool(reports["data"].get("datasets_meeting_20m_floor", 0)) or tokenizer_ready
    blocking: list[str] = []
    for stage, report in reports.items():
        blocking.extend([f"{stage}: {item}" for item in report.get("blocking_failures", [])])

    evaluation_dir = LOCALMAX_TABLES.parent / ("localmax_evaluation_strengthened" if strengthened_evaluation else "localmax_evaluation")
    analysis_dir = LOCALMAX_TABLES.parent / ("localmax_analysis_strengthened" if strengthened_mechanism else "localmax_analysis")
    lm_metrics = _read_csv(evaluation_dir / "lm_metrics.csv")
    lm_summary = _read_csv(evaluation_dir / "stability_results.csv")
    rdc = _read_csv(evaluation_dir / "risk_diversity_cost.csv")
    paired = _read_csv(evaluation_dir / "paired_differences.csv")
    stats = _read_csv(evaluation_dir / "statistical_tests.csv")
    proxy = _read_csv(analysis_dir / "proxy_utility_mismatch.csv")

    if strengthened_evaluation:
        main_rows = [
            {
                "dataset": row["dataset_id"],
                "method": row["method_name"],
                "seed": row["seed"],
                "model_scale": row.get("model_scale", "small"),
                "steps_completed": row["steps_completed"],
                "tokens_seen": row["tokens_seen"],
                "valid_loss": row["valid_loss"],
                "valid_ppl_clipped": row["valid_ppl_clipped"],
                "ppl_clipped": row["ppl_clipped"],
                "ppl_comparable": row["ppl_comparable"],
                "metric_for_comparison": row["metric_for_comparison"],
                "training_manifest": row["training_manifest_path"],
                "evaluation_manifest": "artifacts/localmax_evaluation_strengthened/evaluation_manifest.json",
                "evidence_level": "localmax_training_strengthened",
            }
            for row in lm_metrics
        ]
    else:
        main_rows = [
            {
                "dataset": row["dataset_id"],
                "method": row["method_name"],
                "seed": row["seed"],
                "model_scale": "small",
                "steps_completed": "",
                "tokens_seen": row["tokens_seen"],
                "valid_loss": row["valid_loss"],
                "valid_ppl_clipped": row.get("valid_ppl", ""),
                "ppl_clipped": "",
                "ppl_comparable": "",
                "metric_for_comparison": "valid_loss",
                "training_manifest": row["training_manifest_path"],
                "evaluation_manifest": "artifacts/localmax_evaluation/evaluation_manifest.json",
                "evidence_level": "localmax_training_minimal",
            }
            for row in lm_metrics
        ]
    baseline_rows = [
        {
            "dataset_id": row["dataset_id"],
            "baseline": row.get("method_name", ""),
            "model_scale": "small",
            "seed": "aggregate",
            "metric_name": "mean_valid_loss",
            "metric_value": row["mean_valid_loss"],
            "source_manifest_path": "artifacts/localmax_evaluation_strengthened/evaluation_manifest.json" if strengthened_evaluation else "artifacts/localmax_evaluation/evaluation_manifest.json",
        }
        for row in lm_summary
        if row.get("method_name", "") in {"raw", "exact_dedup", "length_filter"}
    ]
    urd_rows = [
        {
            "dataset_id": row["dataset_id"],
            "ablation": row["comparison"],
            "model_scale": "small",
            "seed": row["seed"],
            "metric_name": "paired_loss_improvement",
            "metric_value": row["paired_loss_improvement"],
            "source_manifest_path": "artifacts/localmax_evaluation_strengthened/paired_differences.csv" if strengthened_evaluation else "artifacts/localmax_evaluation/paired_differences.csv",
        }
        for row in paired
        if "urd_fixed" in row["comparison"]
    ]
    downstream_rows: list[dict[str, str]] = []
    risk_rows = [
        {
            "dataset_id": row["dataset_id"],
            "method": row["method_name"],
            "risk_metric": row.get("mean_risk", row.get("risk", "")),
            "diversity_metric": row.get("mean_diversity", row.get("diversity", "")),
            "cost_metric": row.get("filter_cost_units", row.get("cost", "")),
            "source_manifest_path": "artifacts/localmax_evaluation_strengthened/risk_diversity_cost.csv" if strengthened_evaluation else "artifacts/localmax_evaluation/risk_diversity_cost.csv",
        }
        for row in rdc
    ]
    pareto_rows = [
        {
            "dataset_id": row["dataset_id"],
            "method": row["method_name"],
            "utility": str(-float(row["mean_valid_loss"])) if row.get("mean_valid_loss") else "",
            "risk": row.get("mean_risk", row.get("risk", "")),
            "cost": row.get("filter_cost_units", row.get("cost", "")),
            "pareto_status": "candidate_not_claimed",
            "source_manifest_path": "artifacts/localmax_evaluation_strengthened/risk_diversity_cost.csv" if strengthened_evaluation else "artifacts/localmax_evaluation/risk_diversity_cost.csv",
        }
        for row in rdc
    ]
    mechanism_rows = [
        {
            "dataset_id": row["dataset_id"],
            "method": row["comparison"],
            "analysis_name": "proxy_utility_mismatch",
            "finding": row["finding"],
            "source_manifest_path": "artifacts/localmax_analysis_strengthened/proxy_utility_mismatch.csv" if strengthened_mechanism else "artifacts/localmax_analysis/proxy_utility_mismatch.csv",
        }
        for row in proxy
    ]
    statistical_rows = [
        {
            "dataset_id": row["dataset_id"],
            "comparison": row["comparison"],
            "test_name": row["test_name"],
            "n_seeds": row["n_seeds"],
            "ci_low": row["ci_low"],
            "ci_high": row["ci_high"],
            "significant": row["improvement_claim_allowed"],
            "source_manifest_path": "artifacts/localmax_evaluation_strengthened/statistical_tests.csv" if strengthened_evaluation else "artifacts/localmax_evaluation/statistical_tests.csv",
        }
        for row in stats
    ]
    rows_by_table = {
        "localmax_main_results.csv": main_rows,
        "localmax_baseline_results.csv": baseline_rows,
        "localmax_urd_ablation_results.csv": urd_rows,
        "localmax_downstream_subset_results.csv": downstream_rows,
        "localmax_risk_diversity_cost_results.csv": risk_rows,
        "localmax_pareto_results.csv": pareto_rows,
        "localmax_mechanism_results.csv": mechanism_rows,
        "localmax_statistical_tests.csv": statistical_rows,
    }
    table_status_rows = []
    for filename, fields in TABLES.items():
        rows = rows_by_table.get(filename, [])
        table_path = write_csv(LOCALMAX_TABLES / filename, fields, rows)
        table_status_rows.append(
            {
                "table_name": filename,
                "path": f"artifacts/localmax_tables/{filename}",
                "rows": len(rows),
                "generated_from_manifests": True,
                "empty_reason": "" if rows else "localmax_training_or_evaluation_not_completed" if filename != "localmax_downstream_subset_results.csv" else "downstream_subset_not_run",
                "sha256": "",
            }
        )
        table_status_rows[-1]["sha256"] = _sha256(table_path)
    result_rows_written = sum(row["rows"] for row in table_status_rows)
    minimal_completed = minimal_completed and len(main_rows) > 0
    training_strength_completed = strengthened_completed and len(main_rows) >= 24
    table_status = {
        "step": "step10B_localmax_execution_fix",
        "stage": "localmax_table_generation",
        "status": "completed",
        "created_at": utc_now(),
        "tables": table_status_rows,
        "result_rows_written": result_rows_written,
        "no_fake_metric_values_written": True,
        "completed": True,
        "localmax_training_strengthened_completed": training_strength_completed,
        "localmax_minimal_real_evidence_completed": minimal_completed,
        "localmax_completed": False,
        "level3_completed": False,
        "main_results_modified": False,
    }
    write_json(LOCALMAX_TABLES / "localmax_table_generation_status.json", table_status)
    summary = {
        "step": "step10B_localmax_execution_fix",
        "status": "completed_partial"
        if training_strength_completed or minimal_completed or partial_real
        else "blocked",
        "current_readiness": "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_COMPLETED"
        if training_strength_completed
        else "LOCAL_MAX_PARTIAL_WITH_STRENGTHENED_EVIDENCE"
        if strengthened_partial
        else "LOCAL_MAX_MINIMAL_REAL_EVIDENCE_COMPLETED"
        if minimal_completed
        else "LOCAL_MAX_EXECUTION_BLOCKED_WITH_ACTIONABLE_REASON",
        "created_at": utc_now(),
        "localmax_environment_checked": env_checked,
        "localmax_data_ready": data_ready,
        "localmax_tokenizer_ready": tokenizer_ready,
        "localmax_filters_ready": filters_ready,
        "localmax_small_training_ready": small_ready,
        "localmax_medium_lite_training_ready": medium_lite_ready,
        "localmax_evaluation_ready": evaluation_ready,
        "localmax_downstream_subset_ready": False,
        "localmax_mechanism_ready": mechanism_ready,
        "localmax_registry_finalized": False,
        "localmax_minimal_real_evidence_completed": minimal_completed,
        "localmax_training_strengthened_completed": training_strength_completed,
        "localmax_training_strengthened_partial": strengthened_partial,
        "strengthened_training_runs_completed": strengthened_runs_completed,
        "min_tokens_seen_per_completed_run": strengthened_training.get("min_tokens_seen_per_completed_run", 0),
        "min_steps_completed": strengthened_training.get("min_steps_completed", 0),
        "localmax_completed": False,
        "partial_real_evidence": partial_real,
        "level3_completed": False,
        "level3_completed_artifact": False,
        "true_medium_completed": False,
        "large_lite_completed": False,
        "official_downstream_completed": False,
        "statistical_significance_claim_allowed": False,
        "new_localmax_main_results_added": len(main_rows) > 0,
        "new_training_results_added": small_ready or medium_lite_ready,
        "new_downstream_results_added": False,
        "new_mechanism_results_added": mechanism_ready,
        "main_results_modified": False,
        "historical_results_modified": not protected_hashes_unchanged(),
        "protected_hashes": protected_hashes(),
        "blocking_failures": sorted(set(blocking)),
        "fallbacks_used": [],
        "table_status_path": "artifacts/localmax_tables/localmax_table_generation_status.json",
        "localmax_main_results_rows": len(main_rows),
        "completed_real_training_runs": reports["small_training"].get("completed_real_training_runs", 0),
        "completed_strengthened_training_runs": strengthened_runs_completed,
        "datasets_meeting_20m_floor": reports["data"].get("datasets_meeting_20m_floor", 0),
        "recommended_next_step": "external_review_before_step10C"
        if training_strength_completed
        else "continue_step10B_localmax_training_strengthen"
        if strengthened_partial or strengthened_training
        else "step10B_localmax_expand_methods_or_step10C_after_review"
        if minimal_completed
        else "continue_step10B_localmax_execution",
        "readiness_downgrade_reason": ""
        if training_strength_completed
        else "LocalMax minimal execution has not produced the required non-empty training/evaluation table from real runs.",
        "notes": [
            "Historical main results and run registry were not modified.",
            "LocalMax tables are generated from training/evaluation/mechanism artifacts when available.",
            "This is not a completed Level 3 heavy execution artifact.",
        ],
    }
    write_json(LOCALMAX_REPORTS / "step10B_localmax_execution_summary.json", summary)
    write_markdown(LOCALMAX_REPORTS / "step10B_localmax_execution_summary.md", "Step 10B LocalMax Execution Summary", summary)
    write_report(summary, "step10B_localmax_readiness_report", "Step 10B LocalMax Readiness Report")
    print(json.dumps({"current_readiness": summary["current_readiness"], "localmax_minimal_real_evidence_completed": minimal_completed}))


if __name__ == "__main__":
    main()
