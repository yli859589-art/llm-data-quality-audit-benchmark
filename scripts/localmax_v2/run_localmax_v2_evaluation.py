from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from statistics import mean, pstdev
from typing import Any

from localmax_v2_utils import ROOT, V2_EVALUATION, load_config, load_json, status_payload, write_csv, write_json, write_report


def _completed_training_rows() -> list[dict[str, Any]]:
    report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_training_report.json")
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


def _filter_metrics(dataset_id: str, method: str) -> dict[str, Any]:
    base = ROOT / "artifacts" / "localmax_v2_filters" / dataset_id / method
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
    parser.add_argument("--config", default="configs/localmax_v2/evaluation_matrix.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    rows = _completed_training_rows()
    blocking: list[str] = []
    if len(rows) < int(config["minimum_core_runs"]):
        blocking.append(f"Need {config['minimum_core_runs']} completed V2 training runs; got {len(rows)}.")
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
            "std_valid_nll_nats_per_token": pstdev(losses) if len(losses) > 1 else 0.0,
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
    paired_rows: list[dict[str, Any]] = []
    statistical_rows: list[dict[str, Any]] = []
    by_key = {(str(row["dataset_id"]), str(row["method_name"]), int(row["seed"])): row for row in rows}
    for (dataset_id, method), group in sorted(grouped.items()):
        if method == "raw":
            continue
        diffs = []
        for item in group:
            seed = int(item["seed"])
            raw = by_key.get((dataset_id, "raw", seed))
            if not raw:
                continue
            raw_metric = float(load_json(ROOT / raw["metrics_path"])["valid_nll_nats_per_token"])
            method_metric = float(item["valid_nll_nats_per_token"])
            improvement = raw_metric - method_metric
            diffs.append(improvement)
            paired_rows.append(
                {
                    "dataset_id": dataset_id,
                    "comparison": f"{method}_vs_raw",
                    "seed": seed,
                    "raw_valid_nll": raw_metric,
                    "method_valid_nll": method_metric,
                    "paired_nll_improvement": improvement,
                    "metric_for_comparison": "valid_nll_nats_per_token",
                }
            )
        ci_low, ci_high = _bootstrap_ci(diffs, samples=int(config.get("bootstrap_samples", 1000)))
        allowed = len(diffs) >= 3 and mean(diffs) > 0 and ci_low > 0 and ci_high > 0
        statistical_rows.append(
            {
                "dataset_id": dataset_id,
                "comparison": f"{method}_vs_raw",
                "test_name": "paired_seed_difference_on_valid_nll",
                "n_seeds": len(diffs),
                "mean_paired_nll_improvement": mean(diffs) if diffs else 0.0,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "ci_crosses_zero": ci_low <= 0 <= ci_high,
                "improvement_claim_allowed": allowed,
                "metric_for_comparison": "valid_nll_nats_per_token",
            }
        )
    ranking_rows: list[dict[str, Any]] = []
    pareto_rows: list[dict[str, Any]] = []
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows:
        by_dataset[str(row["dataset_id"])].append(row)
    best_methods: dict[str, str] = {}
    urd_vs_raw: dict[str, dict[str, Any]] = {}
    for dataset_id, group in sorted(by_dataset.items()):
        ranked = sorted(group, key=lambda item: float(item["mean_valid_nll_nats_per_token"]))
        best_methods[dataset_id] = str(ranked[0]["method_name"]) if ranked else ""
        for rank, row in enumerate(ranked, start=1):
            ranking_rows.append(
                {
                    "dataset_id": dataset_id,
                    "rank": rank,
                    "method_name": row["method_name"],
                    "mean_valid_nll_nats_per_token": row["mean_valid_nll_nats_per_token"],
                    "ci_low": row["ci_low"],
                    "ci_high": row["ci_high"],
                    "metric_for_comparison": "valid_nll_nats_per_token",
                }
            )
        for row in risk_rows:
            if row["dataset_id"] != dataset_id:
                continue
            pareto_rows.append(
                {
                    "dataset_id": dataset_id,
                    "method_name": row["method_name"],
                    "utility": -float(row["mean_valid_nll_nats_per_token"]),
                    "risk": row["risk"],
                    "diversity": row["diversity"],
                    "cost": row["cost"],
                    "pareto_scope": "local_diagnostic",
                }
            )
        stat = next((row for row in statistical_rows if row["dataset_id"] == dataset_id and row["comparison"] == "urd_fixed_vs_raw"), None)
        raw = next((row for row in group if row["method_name"] == "raw"), None)
        urd = next((row for row in group if row["method_name"] == "urd_fixed"), None)
        urd_vs_raw[dataset_id] = {
            "urd_mean_lower_than_raw": bool(raw and urd and float(urd["mean_valid_nll_nats_per_token"]) < float(raw["mean_valid_nll_nats_per_token"])),
            "improvement_claim_allowed": bool(stat and stat["improvement_claim_allowed"] is True),
            "ci_crosses_zero": bool(stat and stat["ci_crosses_zero"] is True),
            "mean_paired_nll_improvement": stat["mean_paired_nll_improvement"] if stat else 0.0,
        }
    V2_EVALUATION.mkdir(parents=True, exist_ok=True)
    write_csv(V2_EVALUATION / "lm_metrics.csv", list(lm_rows[0].keys()) if lm_rows else ["dataset_id"], lm_rows)
    write_csv(V2_EVALUATION / "method_summary.csv", list(summary_rows[0].keys()) if summary_rows else ["dataset_id"], summary_rows)
    write_csv(V2_EVALUATION / "paired_differences.csv", list(paired_rows[0].keys()) if paired_rows else ["dataset_id"], paired_rows)
    write_csv(V2_EVALUATION / "bootstrap_confidence_intervals.csv", list(bootstrap_rows[0].keys()) if bootstrap_rows else ["dataset_id"], bootstrap_rows)
    write_csv(V2_EVALUATION / "stability_results.csv", list(summary_rows[0].keys()) if summary_rows else ["dataset_id"], summary_rows)
    write_csv(V2_EVALUATION / "risk_diversity_cost.csv", list(risk_rows[0].keys()) if risk_rows else ["dataset_id"], risk_rows)
    write_csv(V2_EVALUATION / "pareto_results.csv", list(pareto_rows[0].keys()) if pareto_rows else ["dataset_id"], pareto_rows)
    write_csv(V2_EVALUATION / "statistical_tests.csv", list(statistical_rows[0].keys()) if statistical_rows else ["dataset_id"], statistical_rows)
    write_csv(V2_EVALUATION / "method_ranking.csv", list(ranking_rows[0].keys()) if ranking_rows else ["dataset_id"], ranking_rows)
    manifest = {
        "step": "step10B_localmax_v2",
        "scope": "localmax_v2_evaluation",
        "completed": not blocking and bool(lm_rows),
        "metric_for_comparison": "valid_nll_nats_per_token",
        "lm_metrics": "artifacts/localmax_v2_evaluation/lm_metrics.csv",
        "method_summary": "artifacts/localmax_v2_evaluation/method_summary.csv",
        "paired_differences": "artifacts/localmax_v2_evaluation/paired_differences.csv",
        "bootstrap_confidence_intervals": "artifacts/localmax_v2_evaluation/bootstrap_confidence_intervals.csv",
        "stability_results": "artifacts/localmax_v2_evaluation/stability_results.csv",
        "risk_diversity_cost": "artifacts/localmax_v2_evaluation/risk_diversity_cost.csv",
        "pareto_results": "artifacts/localmax_v2_evaluation/pareto_results.csv",
        "statistical_tests": "artifacts/localmax_v2_evaluation/statistical_tests.csv",
        "method_ranking": "artifacts/localmax_v2_evaluation/method_ranking.csv",
        "official_downstream_completed": False,
        "level3_evaluation": False,
    }
    write_json(V2_EVALUATION / "evaluation_manifest.json", manifest)
    ready = not blocking and len(lm_rows) >= int(config["minimum_core_runs"])
    report = status_payload(
        "evaluation",
        ready,
        blocking,
        {
            "status": "completed" if ready else "blocked",
            "current_readiness": "LOCAL_MAX_V2_EVALUATION_COMPLETED" if ready else "LOCAL_MAX_V2_PARTIAL_WITH_REAL_EVIDENCE",
            "localmax_v2_evaluation_ready": ready,
            "evaluation_manifest_path": "artifacts/localmax_v2_evaluation/evaluation_manifest.json",
            "lm_metric_rows": len(lm_rows),
            "aggregate_rows": len(summary_rows),
            "paired_difference_rows": len(paired_rows),
            "statistical_test_rows": len(statistical_rows),
            "metric_for_comparison": "valid_nll_nats_per_token",
            "ppl_valid": all(row["valid_ppl"] != "" for row in lm_rows),
            "ppl_overflow_count": sum(1 for row in lm_rows if str(row["ppl_overflow"]) == "True"),
            "best_method_by_valid_nll": best_methods,
            "urd_fixed_vs_raw": urd_vs_raw,
            "improvement_claim_allowed": any(bool(row["improvement_claim_allowed"]) for row in statistical_rows),
            "official_downstream_completed": False,
            "level3_evaluation": False,
        },
    )
    write_report(report, "localmax_v2_evaluation_report", "LocalMax V2 Evaluation Report")
    print(json.dumps({"localmax_v2_evaluation_ready": ready, "lm_metric_rows": len(lm_rows), "best_method_by_valid_nll": best_methods}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
