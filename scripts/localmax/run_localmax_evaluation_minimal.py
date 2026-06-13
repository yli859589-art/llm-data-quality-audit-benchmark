from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from localmax_utils import (
    LOCALMAX_EVALUATION,
    REPORTS,
    ROOT,
    load_json,
    rel,
    status_payload,
    write_csv,
    write_json,
    write_report,
)


def _load_config(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_training_results() -> list[dict[str, Any]]:
    report = load_json(REPORTS / "localmax_small_training_report.json")
    return [row for row in report.get("training_results", []) if row.get("completed") is True]


def _bootstrap_ci(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return (0.0, 0.0)
    # Deterministic small-sample conservative interval.
    avg = mean(values)
    spread = max(abs(value - avg) for value in values)
    return (avg - spread, avg + spread)


def _write_rows(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    write_csv(path, fields, rows)


def _filter_metrics(dataset_id: str, method: str) -> dict[str, Any]:
    base = ROOT / "artifacts" / "localmax_filters" / dataset_id / method
    risk = load_json(base / "risk_report.json")
    diversity = load_json(base / "diversity_report.json")
    cost = load_json(base / "cost_report.json")
    keep = load_json(base / "keep_rate_report.json")
    return {
        "mean_risk": risk.get("mean_risk", 0.0),
        "mean_diversity": diversity.get("mean_diversity", 0.0),
        "filter_cost_units": cost.get("filter_cost_units", 0),
        "document_keep_rate": keep.get("document_keep_rate", 0.0),
        "token_keep_rate": keep.get("token_keep_rate", 0.0),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax/evaluation_matrix_minimal.yaml")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = _load_config(args.config)
    results = _read_training_results()
    blocking = []
    if not results:
        blocking.append("No completed real LocalMax training runs found.")
    lm_rows = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        grouped[(row["dataset_id"], row["method_name"])].append(row)
        lm_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "method_name": row["method_name"],
                "seed": row["seed"],
                "model_scale": "small",
                "valid_loss": row["valid_loss"],
                "valid_ppl": row["valid_ppl"],
                "tokens_seen": row["tokens_seen"],
                "training_manifest_path": row["training_manifest_path"],
            }
        )
    aggregate_rows = []
    for (dataset_id, method), rows in sorted(grouped.items()):
        losses = [float(row["valid_loss"]) for row in rows]
        ppls = [float(row["valid_ppl"]) for row in rows]
        ci_low, ci_high = _bootstrap_ci(losses)
        aggregate_rows.append(
            {
                "dataset_id": dataset_id,
                "method_name": method,
                "n_seeds": len(rows),
                "mean_valid_loss": mean(losses),
                "mean_valid_ppl": mean(ppls),
                "std_valid_loss": pstdev(losses) if len(losses) > 1 else 0.0,
                "seed_variance": pstdev(losses) ** 2 if len(losses) > 1 else 0.0,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "limited_seed_count": len(rows) < 3,
            }
        )
    paired_rows = []
    statistical_rows = []
    by_dataset_method_seed = {(row["dataset_id"], row["method_name"], int(row["seed"])): row for row in results}
    for (dataset_id, method), rows in sorted(grouped.items()):
        if method == "raw":
            continue
        diffs = []
        for row in rows:
            seed = int(row["seed"])
            raw = by_dataset_method_seed.get((dataset_id, "raw", seed))
            if raw:
                diff = float(raw["valid_loss"]) - float(row["valid_loss"])
                diffs.append(diff)
                paired_rows.append(
                    {
                        "dataset_id": dataset_id,
                        "comparison": f"{method}_vs_raw",
                        "seed": seed,
                        "raw_valid_loss": raw["valid_loss"],
                        "method_valid_loss": row["valid_loss"],
                        "paired_loss_improvement": diff,
                    }
                )
        ci_low, ci_high = _bootstrap_ci(diffs)
        allowed = len(diffs) >= 3 and ci_low > 0 and ci_high > 0
        statistical_rows.append(
            {
                "dataset_id": dataset_id,
                "comparison": f"{method}_vs_raw",
                "test_name": "paired_seed_difference_with_conservative_ci",
                "n_seeds": len(diffs),
                "mean_paired_loss_improvement": mean(diffs) if diffs else 0.0,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "ci_crosses_zero": ci_low <= 0 <= ci_high,
                "improvement_claim_allowed": allowed,
            }
        )
    risk_rows = []
    for row in aggregate_rows:
        metrics = _filter_metrics(str(row["dataset_id"]), str(row["method_name"]))
        risk_rows.append({**row, **metrics})
    ready = bool(results) and bool(aggregate_rows)
    _write_rows(
        LOCALMAX_EVALUATION / "lm_metrics.csv",
        lm_rows,
        ["dataset_id", "method_name", "seed", "model_scale", "valid_loss", "valid_ppl", "tokens_seen", "training_manifest_path"],
    )
    _write_rows(
        LOCALMAX_EVALUATION / "lm_metrics_summary.csv",
        aggregate_rows,
        ["dataset_id", "method_name", "n_seeds", "mean_valid_loss", "mean_valid_ppl", "std_valid_loss", "seed_variance", "ci_low", "ci_high", "limited_seed_count"],
    )
    _write_rows(
        LOCALMAX_EVALUATION / "risk_diversity_cost.csv",
        risk_rows,
        ["dataset_id", "method_name", "n_seeds", "mean_valid_loss", "mean_valid_ppl", "mean_risk", "mean_diversity", "filter_cost_units", "document_keep_rate", "token_keep_rate"],
    )
    _write_rows(
        LOCALMAX_EVALUATION / "stability_results.csv",
        aggregate_rows,
        ["dataset_id", "method_name", "n_seeds", "std_valid_loss", "seed_variance", "limited_seed_count"],
    )
    _write_rows(
        LOCALMAX_EVALUATION / "paired_differences.csv",
        paired_rows,
        ["dataset_id", "comparison", "seed", "raw_valid_loss", "method_valid_loss", "paired_loss_improvement"],
    )
    _write_rows(
        LOCALMAX_EVALUATION / "statistical_tests.csv",
        statistical_rows,
        ["dataset_id", "comparison", "test_name", "n_seeds", "mean_paired_loss_improvement", "ci_low", "ci_high", "ci_crosses_zero", "improvement_claim_allowed"],
    )
    manifest = {
        "step": "step10B_localmax_execution_fix",
        "scope": "localmax_minimal_evaluation",
        "completed": ready,
        "lm_metrics_path": "artifacts/localmax_evaluation/lm_metrics.csv",
        "risk_diversity_cost_path": "artifacts/localmax_evaluation/risk_diversity_cost.csv",
        "stability_results_path": "artifacts/localmax_evaluation/stability_results.csv",
        "paired_differences_path": "artifacts/localmax_evaluation/paired_differences.csv",
        "statistical_tests_path": "artifacts/localmax_evaluation/statistical_tests.csv",
        "local_downstream_subset_ready": bool(config.get("local_downstream_subset_ready", False)),
        "official_downstream_completed": False,
        "level3_evaluation": False,
    }
    write_json(LOCALMAX_EVALUATION / "evaluation_manifest.json", manifest)
    if not ready:
        blocking.append("Evaluation did not produce aggregate rows from real training outputs.")
    report = status_payload(
        "evaluation",
        ready,
        blocking,
        {
            "step": "step10B_localmax_execution_fix",
            "status": "completed" if ready else "blocked",
            "localmax_evaluation_ready": ready,
            "evaluation_manifest_path": "artifacts/localmax_evaluation/evaluation_manifest.json",
            "completed_training_runs_consumed": len(results),
            "aggregate_rows": len(aggregate_rows),
            "paired_difference_rows": len(paired_rows),
            "statistical_test_rows": len(statistical_rows),
            "improvement_claim_allowed": any(row["improvement_claim_allowed"] for row in statistical_rows),
            "local_downstream_subset_ready": False,
            "official_downstream_completed": False,
            "level3_evaluation": False,
            "recommended_next_step": "run_localmax_minimal_mechanism" if ready else "continue_evaluation_execution",
        },
    )
    write_report(report, "localmax_evaluation_report", "LocalMax Minimal Evaluation Report")
    print(json.dumps({"localmax_evaluation_ready": ready, "aggregate_rows": len(aggregate_rows)}))


if __name__ == "__main__":
    main()

