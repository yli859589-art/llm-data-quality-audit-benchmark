from __future__ import annotations

from localmax_utils import LOCALMAX_MECHANISMS, REPORTS, load_json, status_payload, write_json, write_report


def main() -> None:
    evaluation_ready = load_json(REPORTS / "localmax_evaluation_report.json").get("localmax_evaluation_ready") is True
    blocking = [] if evaluation_ready else ["LocalMax evaluation gate is not ready; mechanism analysis is not generated."]
    outputs = {
        "proxy_utility": "blocked_until_localmax_evaluation_ready",
        "overfiltering": "blocked_until_localmax_evaluation_ready",
        "diversity_loss": "blocked_until_localmax_evaluation_ready",
        "domain_shift": "blocked_until_localmax_evaluation_ready",
        "pareto_mechanism": "blocked_until_localmax_evaluation_ready",
        "rank_stability": "protocol_only_not_completed",
        "tokenizer_sensitivity": "protocol_only_not_completed",
        "scale_trend": "protocol_only_not_completed",
        "failure_taxonomy": "historical_negative_results_preserved",
    }
    report = status_payload(
        "mechanism",
        evaluation_ready,
        blocking,
        {
            "localmax_mechanism_ready": evaluation_ready,
            "mechanism_outputs": outputs,
            "full_scale_mechanism_claim_allowed": False,
            "notes": [
                "Mechanism outputs are not promoted without LocalMax evaluation artifacts.",
                "Existing negative results and HDQS++ failure analysis remain preserved.",
            ],
        },
    )
    write_json(LOCALMAX_MECHANISMS / "mechanism_status.json", report)
    write_report(report, "localmax_mechanism_report", "LocalMax Mechanism Report")
    print(f"LocalMax mechanism analysis: ready={evaluation_ready}")


if __name__ == "__main__":
    main()

