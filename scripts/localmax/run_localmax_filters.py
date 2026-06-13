from __future__ import annotations

from localmax_utils import LOCALMAX_FILTERS, REPORTS, load_json, status_payload, write_json, write_report


METHODS = [
    "raw",
    "random_same_keep_rate",
    "exact_dedup",
    "length_filter",
    "c4_style_proxy",
    "gopher_style_proxy",
    "perplexity_proxy",
    "embedding_diversity_proxy",
    "urd_fixed",
    "urd_pareto",
    "urd_ablation_no_risk",
    "urd_ablation_no_diversity",
]


def main() -> None:
    data_report = load_json(REPORTS / "localmax_data_report.json")
    data_ready = data_report.get("localmax_data_ready") is True
    blocking = [] if data_ready else ["LocalMax data gate is not ready; filter matrix is not executed as LocalMax evidence."]
    report = status_payload(
        "filter",
        data_ready,
        blocking,
        {
            "localmax_filters_ready": data_ready,
            "methods_planned": METHODS,
            "methods_completed": METHODS if data_ready else [],
            "proxy_methods_labeled_as_proxy": True,
            "hdqspp_role": "historical_baseline_or_failure_analysis_object",
            "keep_rate_fairness_required": True,
            "filter_manifest_generation_required": True,
            "notes": [
                "No LocalMax filter outputs are promoted when the LocalMax data floor is unmet.",
                "URD outputs from earlier smoke steps are preserved as historical/prototype artifacts only.",
            ],
        },
    )
    write_json(LOCALMAX_FILTERS / "filter_matrix_status.json", report)
    write_report(report, "localmax_filter_report", "LocalMax Filter Report")
    print(f"LocalMax filters: ready={data_ready}")


if __name__ == "__main__":
    main()

