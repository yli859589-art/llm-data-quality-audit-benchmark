from __future__ import annotations

from localmax_utils import LOCALMAX_TRAINING, REPORTS, load_json, status_payload, write_json, write_report


def main() -> None:
    data_ready = load_json(REPORTS / "localmax_data_report.json").get("localmax_data_ready") is True
    filters_ready = load_json(REPORTS / "localmax_filter_report.json").get("localmax_filters_ready") is True
    small_ready = data_ready and filters_ready
    medium_lite_ready = False
    blocking = []
    if not data_ready:
        blocking.append("LocalMax data gate is not ready; small training is not executed.")
    if not filters_ready:
        blocking.append("LocalMax filter gate is not ready; training lineage would be incomplete.")
    blocking.append("Medium-lite is intentionally not marked complete on this 8GB-class local environment.")
    small_report = status_payload(
        "small_training",
        small_ready,
        blocking[:-1] if small_ready else blocking,
        {
            "localmax_small_training_ready": small_ready,
            "small_training_completed": small_ready,
            "minimum_expected_datasets": 2,
            "minimum_expected_methods": 6,
            "minimum_expected_seeds": 3,
            "training_manifest_required": True,
            "checkpoint_manifest_required": True,
            "cost_metadata_required": True,
            "notes": [
                "No PPL or loss values are written without actual LocalMax training manifests.",
            ],
        },
    )
    medium_report = status_payload(
        "medium_lite_training",
        medium_lite_ready,
        ["Medium-lite selected training was not executed locally; true medium is also not complete."],
        {
            "localmax_medium_lite_training_ready": False,
            "medium_lite_completed": False,
            "true_medium_completed": False,
            "large_lite_completed": False,
            "statistical_significance_claim_allowed": False,
            "notes": [
                "Medium-lite remains a selected-run target, not true medium evidence.",
            ],
        },
    )
    write_json(LOCALMAX_TRAINING / "small_training_status.json", small_report)
    write_json(LOCALMAX_TRAINING / "medium_lite_training_status.json", medium_report)
    write_report(small_report, "localmax_small_training_report", "LocalMax Small Training Report")
    write_report(medium_report, "localmax_medium_lite_training_report", "LocalMax Medium-Lite Training Report")
    print(f"LocalMax small training: ready={small_ready}")
    print("LocalMax medium-lite training: ready=False")


if __name__ == "__main__":
    main()

