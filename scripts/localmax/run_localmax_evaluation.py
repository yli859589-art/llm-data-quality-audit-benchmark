from __future__ import annotations

from localmax_utils import LOCALMAX_EVALUATION, REPORTS, load_json, status_payload, write_json, write_report


def main() -> None:
    small_ready = load_json(REPORTS / "localmax_small_training_report.json").get("localmax_small_training_ready") is True
    blocking = [] if small_ready else ["LocalMax training gate is not ready; evaluation metrics are not generated."]
    report = status_payload(
        "evaluation",
        small_ready,
        blocking,
        {
            "localmax_evaluation_ready": small_ready,
            "lm_metrics_ready": small_ready,
            "risk_metrics_ready": small_ready,
            "diversity_metrics_ready": small_ready,
            "cost_metrics_ready": small_ready,
            "pareto_ready": small_ready,
            "downstream_subset_completed": False,
            "official_downstream_completed": False,
            "statistical_significance_claim_allowed": False,
            "notes": [
                "Local downstream subset results are not written without completed LocalMax training manifests.",
                "No official full downstream evaluation is claimed.",
            ],
        },
    )
    write_json(LOCALMAX_EVALUATION / "evaluation_status.json", report)
    write_report(report, "localmax_evaluation_report", "LocalMax Evaluation Report")
    print(f"LocalMax evaluation: ready={small_ready}")


if __name__ == "__main__":
    main()

