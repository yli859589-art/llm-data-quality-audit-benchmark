from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from localmax_utils import ROOT, load_json, status_payload, write_csv, write_json, write_report


OUTPUT_DIR = ROOT / "artifacts" / "localmax_evaluation_strengthened"


def _read_training_results() -> list[dict[str, Any]]:
    report = load_json(ROOT / "artifacts" / "reports" / "localmax_training_strengthened_report.json")
    return [row for row in report.get("training_results", []) if row.get("completed") is True]


def _bootstrap_ci(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        return 0.0, 0.0
    avg = mean(values)
    spread = max(abs(value - avg) for value in values)
    return avg - spread, avg + spread


def _read_filter_metrics(dataset_id: str, method: str) -> dict[str, Any]:
    base = ROOT / "artifacts" / "localmax_filters" / dataset_id / method
    return {
        "risk": load_json(base / "risk_report.json").get("mean_risk", 0.0),
        "diversity": load_json(base / "diversity_report.json").get("mean_diversity", 0.0),
        "cost": load_json(base / "cost_report.json").get("filter_cost_units", 0),
    }


def main() -> None:
    results = _read_training_results()
    blocking = []
    if not results:
        blocking.append("No completed strengthened training runs found.")
    lm_rows = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in results:
        metrics = load_json(ROOT / row["metrics_path"])
        grouped[(row["dataset_id"], row["method_name"])].append({**row, **metrics})
        lm_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "method_name": row["method_name"],
                "seed": row["seed"],
                "model_scale": "small",
                "steps_completed": metrics["steps_completed"],
                "tokens_seen": metrics["tokens_seen"],
                "valid_loss": metrics["valid_loss"],
                "valid_ppl_raw": "" if metrics["valid_ppl_raw"] is None else metrics["valid_ppl_raw"],
                "valid_ppl_clipped": metrics["valid_ppl_clipped"],
                "ppl_clipped": metrics["ppl_clipped"],
                "ppl_comparable": metrics["ppl_comparable"],
                "metric_for_comparison": "valid_loss",
                "training_manifest_path": row["training_manifest_path"],
            }
        )
    summary_rows = []
    risk_rows = []
    for (dataset_id, method), rows in sorted(grouped.items()):
        losses = [float(row["valid_loss"]) for row in rows]
        clipped = [bool(row["ppl_clipped"]) for row in rows]
        clipped_ppls = [float(row["valid_ppl_clipped"]) for row in rows]
        ci_low, ci_high = _bootstrap_ci(losses)
        filter_metrics = _read_filter_metrics(dataset_id, method)
        summary = {
            "dataset_id": dataset_id,
            "method_name": method,
            "n_seeds": len(rows),
            "mean_valid_loss": mean(losses),
            "std_valid_loss": pstdev(losses) if len(losses) > 1 else 0.0,
            "mean_valid_ppl_clipped": mean(clipped_ppls),
            "num_ppl_clipped": sum(1 for item in clipped if item),
            "ppl_comparable": not all(clipped),
            "seed_variance": pstdev(losses) ** 2 if len(losses) > 1 else 0.0,
            "ci_low_valid_loss": ci_low,
            "ci_high_valid_loss": ci_high,
            "metric_for_comparison": "valid_loss",
        }
        summary_rows.append(summary)
        risk_rows.append({**summary, **filter_metrics})
    paired_rows = []
    statistical_rows = []
    by_key = {(row["dataset_id"], row["method_name"], int(row["seed"])): row for row in results}
    for (dataset_id, method), rows in sorted(grouped.items()):
        if method == "raw":
            continue
        diffs = []
        for row in rows:
            seed = int(row["seed"])
            raw = by_key.get((dataset_id, "raw", seed))
            if not raw:
                continue
            raw_loss = float(load_json(ROOT / raw["metrics_path"])["valid_loss"])
            method_loss = float(row["valid_loss"])
            diff = raw_loss - method_loss
            diffs.append(diff)
            paired_rows.append(
                {
                    "dataset_id": dataset_id,
                    "comparison": f"{method}_vs_raw",
                    "seed": seed,
                    "raw_valid_loss": raw_loss,
                    "method_valid_loss": method_loss,
                    "paired_loss_improvement": diff,
                    "metric_for_comparison": "valid_loss",
                }
            )
        ci_low, ci_high = _bootstrap_ci(diffs)
        allowed = len(diffs) >= 3 and mean(diffs) > 0 and ci_low > 0 and ci_high > 0
        statistical_rows.append(
            {
                "dataset_id": dataset_id,
                "comparison": f"{method}_vs_raw",
                "test_name": "paired_seed_difference_on_valid_loss",
                "n_seeds": len(diffs),
                "mean_paired_loss_improvement": mean(diffs) if diffs else 0.0,
                "ci_low": ci_low,
                "ci_high": ci_high,
                "ci_crosses_zero": ci_low <= 0 <= ci_high,
                "improvement_claim_allowed": allowed,
                "metric_for_comparison": "valid_loss",
            }
        )
    ranking_rows = []
    by_dataset: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in summary_rows:
        by_dataset[str(row["dataset_id"])].append(row)
    best_methods = {}
    urd_analysis = {}
    for dataset_id, rows in sorted(by_dataset.items()):
        ranked = sorted(rows, key=lambda item: float(item["mean_valid_loss"]))
        best_methods[dataset_id] = ranked[0]["method_name"] if ranked else ""
        for rank, row in enumerate(ranked, start=1):
            ranking_rows.append(
                {
                    "dataset_id": dataset_id,
                    "rank": rank,
                    "method_name": row["method_name"],
                    "mean_valid_loss": row["mean_valid_loss"],
                    "metric_for_comparison": "valid_loss",
                }
            )
        raw = next((row for row in rows if row["method_name"] == "raw"), None)
        urd = next((row for row in rows if row["method_name"] == "urd_fixed"), None)
        stat = next((row for row in statistical_rows if row["dataset_id"] == dataset_id and row["comparison"] == "urd_fixed_vs_raw"), None)
        urd_analysis[dataset_id] = {
            "urd_fixed_beats_raw_by_valid_loss": bool(raw and urd and float(urd["mean_valid_loss"]) < float(raw["mean_valid_loss"])),
            "ci_supports_urd_claim": bool(stat and stat["improvement_claim_allowed"] is True),
            "improvement_claim_allowed": bool(stat and stat["improvement_claim_allowed"] is True),
        }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv(
        OUTPUT_DIR / "lm_metrics.csv",
        [
            "dataset_id",
            "method_name",
            "seed",
            "model_scale",
            "steps_completed",
            "tokens_seen",
            "valid_loss",
            "valid_ppl_raw",
            "valid_ppl_clipped",
            "ppl_clipped",
            "ppl_comparable",
            "metric_for_comparison",
            "training_manifest_path",
        ],
        lm_rows,
    )
    write_csv(
        OUTPUT_DIR / "stability_results.csv",
        [
            "dataset_id",
            "method_name",
            "n_seeds",
            "mean_valid_loss",
            "std_valid_loss",
            "mean_valid_ppl_clipped",
            "num_ppl_clipped",
            "ppl_comparable",
            "seed_variance",
            "metric_for_comparison",
        ],
        summary_rows,
    )
    write_csv(
        OUTPUT_DIR / "paired_differences.csv",
        ["dataset_id", "comparison", "seed", "raw_valid_loss", "method_valid_loss", "paired_loss_improvement", "metric_for_comparison"],
        paired_rows,
    )
    write_csv(
        OUTPUT_DIR / "statistical_tests.csv",
        [
            "dataset_id",
            "comparison",
            "test_name",
            "n_seeds",
            "mean_paired_loss_improvement",
            "ci_low",
            "ci_high",
            "ci_crosses_zero",
            "improvement_claim_allowed",
            "metric_for_comparison",
        ],
        statistical_rows,
    )
    write_csv(
        OUTPUT_DIR / "method_ranking.csv",
        ["dataset_id", "rank", "method_name", "mean_valid_loss", "metric_for_comparison"],
        ranking_rows,
    )
    write_csv(
        OUTPUT_DIR / "risk_diversity_cost.csv",
        [
            "dataset_id",
            "method_name",
            "n_seeds",
            "mean_valid_loss",
            "mean_valid_ppl_clipped",
            "risk",
            "diversity",
            "cost",
            "metric_for_comparison",
        ],
        risk_rows,
    )
    manifest = {
        "step": "step10B_localmax_training_strengthen",
        "scope": "localmax_evaluation_strengthened",
        "completed": bool(lm_rows),
        "lm_metrics_path": "artifacts/localmax_evaluation_strengthened/lm_metrics.csv",
        "paired_differences_path": "artifacts/localmax_evaluation_strengthened/paired_differences.csv",
        "stability_results_path": "artifacts/localmax_evaluation_strengthened/stability_results.csv",
        "statistical_tests_path": "artifacts/localmax_evaluation_strengthened/statistical_tests.csv",
        "method_ranking_path": "artifacts/localmax_evaluation_strengthened/method_ranking.csv",
        "metric_for_comparison": "valid_loss",
        "official_downstream_completed": False,
        "level3_evaluation": False,
    }
    write_json(OUTPUT_DIR / "evaluation_manifest.json", manifest)
    all_ppl_clipped = bool(lm_rows) and all(str(row["ppl_clipped"]) == "True" or row["ppl_clipped"] is True for row in lm_rows)
    report = status_payload(
        "evaluation_strengthened",
        bool(lm_rows),
        blocking,
        {
            "step": "step10B_localmax_training_strengthen",
            "status": "completed" if lm_rows else "blocked",
            "localmax_evaluation_strengthened_ready": bool(lm_rows),
            "evaluation_manifest_path": "artifacts/localmax_evaluation_strengthened/evaluation_manifest.json",
            "lm_metric_rows": len(lm_rows),
            "aggregate_rows": len(summary_rows),
            "paired_difference_rows": len(paired_rows),
            "statistical_test_rows": len(statistical_rows),
            "all_ppl_clipped": all_ppl_clipped,
            "ppl_comparable": not all_ppl_clipped,
            "metric_for_comparison": "valid_loss",
            "best_method_by_valid_loss": best_methods,
            "urd_fixed_vs_raw": urd_analysis,
            "improvement_claim_allowed": any(bool(row["improvement_claim_allowed"]) for row in statistical_rows),
            "official_downstream_completed": False,
            "level3_evaluation": False,
            "notes": [
                "PPL is reported with clipping metadata; method comparisons use valid_loss.",
                "Clipped PPL is not used for improvement claims.",
            ],
        },
    )
    write_report(report, "localmax_evaluation_strengthened_report", "LocalMax Evaluation Strengthened Report")
    print(json.dumps({"localmax_evaluation_strengthened_ready": bool(lm_rows), "lm_metric_rows": len(lm_rows)}))


if __name__ == "__main__":
    main()

