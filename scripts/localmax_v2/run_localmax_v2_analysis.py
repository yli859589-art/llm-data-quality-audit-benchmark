from __future__ import annotations

import argparse
import json
from collections import defaultdict
from statistics import mean

from localmax_v2_utils import ROOT, V2_ANALYSIS, load_config, read_csv, status_payload, write_csv, write_json, write_report


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    return 0.0 if value == "" else float(value)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax_v2/mechanism_matrix.yaml")
    args = parser.parse_args()
    _ = load_config(args.config)
    summary = read_csv(ROOT / "artifacts" / "localmax_v2_evaluation" / "method_summary.csv")
    risk = read_csv(ROOT / "artifacts" / "localmax_v2_evaluation" / "risk_diversity_cost.csv")
    stats = read_csv(ROOT / "artifacts" / "localmax_v2_evaluation" / "statistical_tests.csv")
    ranking = read_csv(ROOT / "artifacts" / "localmax_v2_evaluation" / "method_ranking.csv")
    blocking: list[str] = []
    if not summary or not risk or not stats:
        blocking.append("V2 mechanism analysis requires non-empty evaluation tables.")
    V2_ANALYSIS.mkdir(parents=True, exist_ok=True)
    proxy_rows = []
    overfilter_rows = []
    diversity_rows = []
    rank_rows = []
    urd_rows = []
    failure_rows = []
    by_dataset: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in risk:
        by_dataset[row["dataset_id"]].append(row)
        proxy_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "method_name": row["method_name"],
                "proxy_utility": -_float(row, "risk") + _float(row, "diversity"),
                "observed_utility": -_float(row, "mean_valid_nll_nats_per_token"),
                "mismatch_note": "local diagnostic; lower NLL is better",
            }
        )
        overfilter_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "method_name": row["method_name"],
                "token_keep_rate": row["token_keep_rate"],
                "mean_valid_nll_nats_per_token": row["mean_valid_nll_nats_per_token"],
                "overfiltering_risk": float(row["token_keep_rate"]) < 0.7,
            }
        )
        diversity_rows.append(
            {
                "dataset_id": row["dataset_id"],
                "method_name": row["method_name"],
                "diversity": row["diversity"],
                "token_keep_rate": row["token_keep_rate"],
                "diversity_loss_proxy": 1.0 - _float(row, "diversity"),
            }
        )
    for dataset_id, rows in by_dataset.items():
        raw = next((row for row in rows if row["method_name"] == "raw"), None)
        urd = next((row for row in rows if row["method_name"] == "urd_fixed"), None)
        dedup = next((row for row in rows if row["method_name"] == "exact_dedup"), None)
        if raw and urd:
            stat = next((row for row in stats if row["dataset_id"] == dataset_id and row["comparison"] == "urd_fixed_vs_raw"), {})
            urd_rows.append(
                {
                    "dataset_id": dataset_id,
                    "comparison": "urd_fixed_vs_raw",
                    "raw_mean_nll": raw["mean_valid_nll_nats_per_token"],
                    "urd_mean_nll": urd["mean_valid_nll_nats_per_token"],
                    "mean_paired_nll_improvement": stat.get("mean_paired_nll_improvement", "0"),
                    "ci_low": stat.get("ci_low", "0"),
                    "ci_high": stat.get("ci_high", "0"),
                    "improvement_claim_allowed": stat.get("improvement_claim_allowed", "False"),
                }
            )
        if dedup and urd:
            urd_rows.append(
                {
                    "dataset_id": dataset_id,
                    "comparison": "urd_fixed_vs_exact_dedup",
                    "raw_mean_nll": dedup["mean_valid_nll_nats_per_token"],
                    "urd_mean_nll": urd["mean_valid_nll_nats_per_token"],
                    "mean_paired_nll_improvement": "",
                    "ci_low": "",
                    "ci_high": "",
                    "improvement_claim_allowed": False,
                }
            )
    by_method: dict[str, list[int]] = defaultdict(list)
    for row in ranking:
        by_method[row["method_name"]].append(int(row["rank"]))
    for method, ranks in sorted(by_method.items()):
        rank_rows.append(
            {
                "method_name": method,
                "mean_rank": mean(ranks),
                "rank_range": max(ranks) - min(ranks),
                "rank_stability_note": "lower rank is better; local two-dataset diagnostic",
            }
        )
    for row in stats:
        if row["comparison"] == "urd_fixed_vs_raw" and row["improvement_claim_allowed"] != "True":
            failure_rows.append(
                {
                    "dataset_id": row["dataset_id"],
                    "failure_type": "urd_claim_not_supported",
                    "reason": "CI crosses zero or mean paired improvement is not strictly supported.",
                    "comparison": row["comparison"],
                }
            )
    scale_rows = [
        {
            "model_scale": "small",
            "completed": True,
            "parameter_count": load_config("artifacts/reports/localmax_v2_training_report.json").get("parameter_count", ""),
            "tokens_seen_per_run_floor": 1000000,
            "true_medium_completed": False,
            "large_lite_completed": False,
        }
    ]
    domain_rows = []
    for dataset_id, rows in by_dataset.items():
        domain_rows.append(
            {
                "dataset_id": dataset_id,
                "best_method": min(rows, key=lambda item: _float(item, "mean_valid_nll_nats_per_token"))["method_name"],
                "mean_nll_across_methods": mean(_float(row, "mean_valid_nll_nats_per_token") for row in rows),
                "dataset_dependent_effects": True,
            }
        )
    write_csv(V2_ANALYSIS / "proxy_utility_mismatch.csv", list(proxy_rows[0].keys()) if proxy_rows else ["dataset_id"], proxy_rows)
    write_csv(V2_ANALYSIS / "overfiltering_report.csv", list(overfilter_rows[0].keys()) if overfilter_rows else ["dataset_id"], overfilter_rows)
    write_csv(V2_ANALYSIS / "diversity_loss_report.csv", list(diversity_rows[0].keys()) if diversity_rows else ["dataset_id"], diversity_rows)
    write_csv(V2_ANALYSIS / "domain_shift_report.csv", list(domain_rows[0].keys()) if domain_rows else ["dataset_id"], domain_rows)
    write_csv(V2_ANALYSIS / "keep_rate_fairness.csv", ["dataset_id", "method_name", "token_keep_rate", "mean_valid_nll_nats_per_token", "overfiltering_risk"], overfilter_rows)
    write_csv(V2_ANALYSIS / "rank_stability_report.csv", list(rank_rows[0].keys()) if rank_rows else ["method_name"], rank_rows)
    write_csv(V2_ANALYSIS / "urd_comparison_report.csv", list(urd_rows[0].keys()) if urd_rows else ["dataset_id"], urd_rows)
    write_csv(V2_ANALYSIS / "scale_trend_protocol.csv", list(scale_rows[0].keys()), scale_rows)
    write_csv(V2_ANALYSIS / "failure_taxonomy.csv", list(failure_rows[0].keys()) if failure_rows else ["dataset_id", "failure_type", "reason", "comparison"], failure_rows)
    manifest = {
        "step": "step10B_localmax_v2",
        "scope": "localmax_v2_mechanism",
        "completed": not blocking,
        "analysis_files": {
            "proxy_utility_mismatch": "artifacts/localmax_v2_analysis/proxy_utility_mismatch.csv",
            "overfiltering": "artifacts/localmax_v2_analysis/overfiltering_report.csv",
            "diversity_loss": "artifacts/localmax_v2_analysis/diversity_loss_report.csv",
            "domain_shift": "artifacts/localmax_v2_analysis/domain_shift_report.csv",
            "keep_rate_fairness": "artifacts/localmax_v2_analysis/keep_rate_fairness.csv",
            "rank_stability": "artifacts/localmax_v2_analysis/rank_stability_report.csv",
            "urd_comparison": "artifacts/localmax_v2_analysis/urd_comparison_report.csv",
            "scale_trend": "artifacts/localmax_v2_analysis/scale_trend_protocol.csv",
            "failure_taxonomy": "artifacts/localmax_v2_analysis/failure_taxonomy.csv",
        },
        "full_scale_causal_conclusion": False,
    }
    write_json(V2_ANALYSIS / "mechanism_manifest.json", manifest)
    report = status_payload(
        "mechanism",
        not blocking,
        blocking,
        {
            "status": "completed" if not blocking else "blocked",
            "current_readiness": "LOCAL_MAX_V2_MECHANISM_COMPLETED" if not blocking else "LOCAL_MAX_V2_PARTIAL_WITH_REAL_EVIDENCE",
            "localmax_v2_mechanism_ready": not blocking,
            "proxy_utility_rows": len(proxy_rows),
            "overfiltering_rows": len(overfilter_rows),
            "diversity_loss_rows": len(diversity_rows),
            "rank_stability_rows": len(rank_rows),
            "failure_taxonomy_rows": len(failure_rows),
            "mechanism_manifest_path": "artifacts/localmax_v2_analysis/mechanism_manifest.json",
        },
    )
    write_report(report, "localmax_v2_mechanism_report", "LocalMax V2 Mechanism Report")
    print(json.dumps({"localmax_v2_mechanism_ready": not blocking, "failure_taxonomy_rows": len(failure_rows)}))
    if blocking:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
