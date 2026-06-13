from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from statistics import mean
from typing import Any

from ccfc_utils import CCFC_EVALUATION, CCFC_FILTERS, CCFC_TABLES, ROOT, load_config, load_json, status_payload, write_csv, write_json, write_report


def _completed_training_rows() -> list[dict[str, Any]]:
    report = load_json(ROOT / "artifacts" / "reports" / "localmax_ccfc_training_report.json")
    return [row for row in report.get("training_results", []) if row.get("completed") is True]


def _bootstrap_ci(values: list[float], *, samples: int = 1000, seed: int = 13) -> tuple[float, float]:
    if len(values) < 2:
        return (values[0], values[0]) if values else (0.0, 0.0)
    rng = random.Random(seed)
    boots = []
    for _ in range(samples):
        draw = [values[rng.randrange(len(values))] for _ in values]
        boots.append(mean(draw))
    boots.sort()
    return boots[int(0.025 * (samples - 1))], boots[int(0.975 * (samples - 1))]


def _pstdev(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    avg = sum(values) / len(values)
    return (sum((value - avg) ** 2 for value in values) / len(values)) ** 0.5


def _filter_metrics(dataset_id: str, method: str) -> dict[str, Any]:
    base = CCFC_FILTERS / dataset_id / method
    risk = load_json(base / "risk_report.json")
    diversity = load_json(base / "diversity_report.json")
    cost = load_json(base / "cost_report.json")
    keep = load_json(base / "keep_rate_report.json")
    return {
        "risk": risk.get("mean_risk", 0.0),
        "diversity": diversity.get("mean_diversity", 0.0),
        "cost": cost.get("filter_cost_units", 0),
        "document_keep_rate": keep.get("document_keep_rate", 0.0),
        "token_keep_rate": keep.get("token_keep_rate", 0.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax_ccfc/evaluation_matrix.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    rows = _completed_training_rows()
    blocking: list[str] = []
    if len(rows) < int(config["minimum_core_runs"]):
        blocking.append(f"Need {config['minimum_core_runs']} completed CCF-C training runs; got {len(rows)}.")
    lm_rows: list[dict[str, Any]] = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        metrics = load_json(ROOT / row["metrics_path"])
        merged = {**row, **metrics}
        grouped[(str(row["dataset_id"]), str(row["method_name"]))].append(merged)
        lm_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "method_name": row["method_name"],
                "seed": row["seed"],
                "model_scale": "small",
                "steps_completed": metrics["steps_completed"],
                "tokens_seen": metrics["tokens_seen"],
                "valid_nll_nats_per_token": metrics["valid_nll_nats_per_token"],
                "valid_loss": metrics["valid_loss"],
                "valid_log_ppl": metrics["valid_log_ppl"],
                "valid_ppl": "" if metrics["valid_ppl"] is None else metrics["valid_ppl"],
                "ppl_overflow": metrics["ppl_overflow"],
                "metric_for_comparison": "valid_nll_nats_per_token",
                "training_manifest_path": row["training_manifest_path"],
            }
        )
    summary_rows: list[dict[str, Any]] = []
    bootstrap_rows: list[dict[str, Any]] = []
    risk_rows: list[dict[str, Any]] = []
    for (dataset_id, method), group in sorted(grouped.items()):
        losses = [float(item["valid_nll_nats_per_token"]) for item in group]
        ci_low, ci_high = _bootstrap_ci(losses, samples=int(config.get("bootstrap_samples", 1000)))
        summary = {
            "dataset_id": dataset_id,
            "method_name": method,
            "n_seeds": len(group),
            "mean_valid_nll_nats_per_token": mean(losses),
            "std_valid_nll_nats_per_token": _pstdev(losses),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "mean_valid_log_ppl": mean([float(item["valid_log_ppl"]) for item in group]),
            "mean_valid_ppl": mean([float(item["valid_ppl"]) for item in group if item.get("valid_ppl") is not None])
            if all(item.get("valid_ppl") is not None for item in group)
            else "",
            "ppl_overflow_count": sum(1 for item in group if bool(item.get("ppl_overflow"))),
            "metric_for_comparison": "valid_nll_nats_per_token",
        }
        summary_rows.append(summary)
        bootstrap_rows.append(
            {
                "dataset_id": dataset_id,
                "method_name": method,
                "metric": "valid_nll_nats_per_token",
                "ci_low": ci_low,
                "ci_high": ci_high,
                "n_seeds": len(group),
                "bootstrap_samples": int(config.get("bootstrap_samples", 1000)),
            }
        )
        risk_rows.append({**summary, **_filter_metrics(dataset_id, method)})
    statistical_rows: list[dict[str, Any]] = []
    by_key = {(str(row["dataset_id"]), str(row["method_name"]), int(row["seed"])): row for row in rows}
    for (dataset_id, method), group in sorted(grouped.items()):
        if method == "raw":
            continue
        diffs = []
        for item in group:
            seed = int(item["seed"])
            raw = by_key.get((dataset_id, "raw", seed))
            if raw:
                raw_metrics = load_json(ROOT / raw["metrics_path"])
                method_metrics = load_json(ROOT / item["metrics_path"])
                diffs.append(float(raw_metrics["valid_nll_nats_per_token"]) - float(method_metrics["valid_nll_nats_per_token"]))
        ci_low, ci_high = _bootstrap_ci(diffs, samples=int(config.get("bootstrap_samples", 1000))) if diffs else (0.0, 0.0)
        mean_diff = mean(diffs) if diffs else 0.0
        statistical_rows.append(
            {
                "dataset_id": dataset_id,
                "comparison": f"{method}_vs_raw",
                "test_name": "paired_seed_difference_on_valid_nll",
                "n_seeds": len(diffs),
                "mean_paired_nll_improvement": mean_diff,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "ci_crosses_zero": ci_low <= 0 <= ci_high,
                "improvement_claim_allowed": (ci_low > 0 and mean_diff > 0),
                "metric_for_comparison": "valid_nll_nats_per_token",
            }
        )
    ranking_rows = []
    for dataset_id in sorted({row["dataset_id"] for row in summary_rows}):
        dataset_rows = [row for row in summary_rows if row["dataset_id"] == dataset_id]
        for rank, row in enumerate(sorted(dataset_rows, key=lambda item: float(item["mean_valid_nll_nats_per_token"])), 1):
            ranking_rows.append({"dataset_id": dataset_id, "method_name": row["method_name"], "rank": rank, "metric": "valid_nll_nats_per_token"})
    CCFC_EVALUATION.mkdir(parents=True, exist_ok=True)
    CCFC_TABLES.mkdir(parents=True, exist_ok=True)
    fields_lm = ["dataset_id", "method_name", "seed", "model_scale", "steps_completed", "tokens_seen", "valid_nll_nats_per_token", "valid_loss", "valid_log_ppl", "valid_ppl", "ppl_overflow", "metric_for_comparison", "training_manifest_path"]
    fields_summary = ["dataset_id", "method_name", "n_seeds", "mean_valid_nll_nats_per_token", "std_valid_nll_nats_per_token", "ci_low", "ci_high", "mean_valid_log_ppl", "mean_valid_ppl", "ppl_overflow_count", "metric_for_comparison"]
    fields_stats = ["dataset_id", "comparison", "test_name", "n_seeds", "mean_paired_nll_improvement", "ci_low", "ci_high", "ci_crosses_zero", "improvement_claim_allowed", "metric_for_comparison"]
    fields_risk = fields_summary + ["risk", "diversity", "cost", "document_keep_rate", "token_keep_rate"]
    write_csv(CCFC_EVALUATION / "lm_metrics.csv", fields_lm, lm_rows)
    write_csv(CCFC_EVALUATION / "method_summary.csv", fields_summary, summary_rows)
    write_csv(CCFC_EVALUATION / "statistical_tests.csv", fields_stats, statistical_rows)
    write_csv(CCFC_EVALUATION / "risk_diversity_cost.csv", fields_risk, risk_rows)
    write_csv(CCFC_EVALUATION / "method_ranking.csv", ["dataset_id", "method_name", "rank", "metric"], ranking_rows)
    write_csv(CCFC_TABLES / "ccfc_main_results.csv", fields_lm, lm_rows)
    write_csv(CCFC_TABLES / "ccfc_method_summary.csv", fields_summary, summary_rows)
    write_csv(CCFC_TABLES / "ccfc_statistical_tests.csv", fields_stats, statistical_rows)
    write_csv(CCFC_TABLES / "ccfc_risk_diversity_cost.csv", fields_risk, risk_rows)
    write_csv(CCFC_TABLES / "ccfc_method_ranking.csv", ["dataset_id", "method_name", "rank", "metric"], ranking_rows)
    best = {}
    for dataset_id in sorted({row["dataset_id"] for row in summary_rows}):
        dataset_rows = [row for row in summary_rows if row["dataset_id"] == dataset_id]
        if dataset_rows:
            best[dataset_id] = min(dataset_rows, key=lambda item: float(item["mean_valid_nll_nats_per_token"]))["method_name"]
    ready = not blocking
    manifest = {
        "step": "localmax_ccfc_strengthening",
        "scope": "ccfc_evaluation",
        "completed": ready,
        "metric_for_comparison": "valid_nll_nats_per_token",
        "lm_metrics": "artifacts/localmax_ccfc_evaluation/lm_metrics.csv",
        "method_summary": "artifacts/localmax_ccfc_evaluation/method_summary.csv",
        "statistical_tests": "artifacts/localmax_ccfc_evaluation/statistical_tests.csv",
        "claim_allowed": ready,
    }
    write_json(CCFC_EVALUATION / "evaluation_manifest.json", manifest)
    report = status_payload(
        "evaluation",
        ready,
        blocking,
        {
            "status": "completed" if ready else "blocked",
            "current_readiness": "CCFC_EVALUATION_COMPLETED" if ready else "CCFC_PARTIAL_EVIDENCE",
            "ccfc_evaluation_ready": ready,
            "lm_metric_rows": len(lm_rows),
            "aggregate_rows": len(summary_rows),
            "statistical_test_rows": len(statistical_rows),
            "best_method_by_valid_nll": best,
            "metric_for_comparison": "valid_nll_nats_per_token",
            "ppl_valid": all(str(row.get("ppl_overflow")) == "False" for row in lm_rows),
            "recommended_next_step": "run_ccfc_downstream" if ready else "continue_ccfc_training",
        },
    )
    write_report(report, "localmax_ccfc_evaluation_report", "LocalMax CCF-C Evaluation Report")
    print(json.dumps({"ccfc_evaluation_ready": ready, "lm_metric_rows": len(lm_rows), "best_method_by_valid_nll": best}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
