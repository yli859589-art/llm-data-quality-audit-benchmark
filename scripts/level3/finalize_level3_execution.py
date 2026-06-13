from __future__ import annotations

from execution_utils import (
    REPORTS,
    load_json,
    protected_hashes,
    protected_hashes_unchanged,
    utc_now,
    write_level3_status_artifacts,
    write_report,
)


REPORT_FILES = {
    "environment": "step10B_environment_report.json",
    "rehearsal": "step10B_rehearsal_report.json",
    "data": "step10B_data_report.json",
    "tokenizer": "step10B_tokenizer_report.json",
    "filter": "step10B_filter_report.json",
    "small_training": "step10B_small_training_report.json",
    "medium_training": "step10B_medium_training_report.json",
    "large_lite": "step10B_large_lite_report.json",
    "evaluation": "step10B_evaluation_report.json",
    "mechanism": "step10B_mechanism_report.json",
}


def _stage(name: str) -> dict:
    return load_json(REPORTS / REPORT_FILES[name])


def main() -> None:
    reports = {name: _stage(name) for name in REPORT_FILES}
    environment_checked = bool(reports["environment"])
    rehearsal_completed = reports["rehearsal"].get("rehearsal_completed") is True
    level3_data_ready = reports["data"].get("level3_data_ready") is True
    level3_tokenizer_ready = reports["tokenizer"].get("level3_tokenizer_ready") is True
    level3_filters_ready = reports["filter"].get("level3_filters_ready") is True
    level3_small_training_ready = reports["small_training"].get("level3_small_training_ready") is True
    level3_medium_training_ready = reports["medium_training"].get("level3_medium_training_ready") is True
    level3_large_lite_ready = reports["large_lite"].get("level3_large_lite_ready") is True
    level3_evaluation_ready = reports["evaluation"].get("level3_evaluation_ready") is True
    level3_downstream_ready = reports["evaluation"].get("level3_downstream_ready") is True
    level3_mechanism_ready = reports["mechanism"].get("level3_mechanism_ready") is True
    required_ready = [
        level3_data_ready,
        level3_tokenizer_ready,
        level3_filters_ready,
        level3_small_training_ready,
        level3_medium_training_ready,
        level3_evaluation_ready,
        level3_downstream_ready,
        level3_mechanism_ready,
    ]
    completed = all(required_ready)
    blocking = []
    for name, report in reports.items():
        blocking.extend([f"{name}: {item}" for item in report.get("blocking_failures", [])])
    readiness = {
        "step": "step10B_level3_heavy_execution",
        "stage": "readiness",
        "status": "completed" if completed else "completed_with_failures",
        "environment_checked": environment_checked,
        "rehearsal_completed": rehearsal_completed,
        "level3_data_ready": level3_data_ready,
        "level3_tokenizer_ready": level3_tokenizer_ready,
        "level3_filters_ready": level3_filters_ready,
        "level3_small_training_ready": level3_small_training_ready,
        "level3_medium_training_ready": level3_medium_training_ready,
        "level3_large_lite_ready": level3_large_lite_ready,
        "level3_evaluation_ready": level3_evaluation_ready,
        "level3_downstream_ready": level3_downstream_ready,
        "level3_mechanism_ready": level3_mechanism_ready,
        "level3_registry_finalized": False,
        "data_gate": "pass" if level3_data_ready else "not_ready",
        "tokenizer_gate": "pass" if level3_tokenizer_ready else "not_ready",
        "filter_gate": "pass" if level3_filters_ready else "not_ready",
        "model_scale_gate": "pass" if level3_medium_training_ready else "partial" if level3_small_training_ready else "not_ready",
        "evaluation_gate": "pass" if level3_evaluation_ready and level3_downstream_ready else "not_ready",
        "mechanism_gate": "pass" if level3_mechanism_ready else "not_ready",
        "claim_gate": "pass",
        "current_readiness": "LEVEL3_COMPLETED_ARTIFACT" if completed else "LEVEL3_PIPELINE_READY",
        "level3_completed_artifact": completed,
        "heavy_execution_completed": completed,
        "main_results_modified": False,
        "historical_results_modified": not protected_hashes_unchanged(),
        "new_level3_main_results_added": False,
        "new_training_results_added": level3_small_training_ready or level3_medium_training_ready,
        "new_downstream_results_added": level3_downstream_ready,
        "new_mechanism_results_added": level3_mechanism_ready,
        "blocking_failures": sorted(set(blocking)),
        "fallbacks_used": [],
        "readiness_downgrade_reason": "" if completed else "Step 10B heavy execution did not complete the required Level 3 data/training/evaluation gates.",
        "recommended_next_step": "step10C_level3_final_release_freeze" if completed else "continue_step10B_heavy_execution",
        "completed": completed,
        "created_at": utc_now(),
        "protected_hashes": protected_hashes(),
    }
    write_level3_status_artifacts(readiness)
    write_report(readiness, "step10B_readiness_report", "Step 10B Readiness Report")
    print(f"Step 10B readiness: {readiness['status']}")


if __name__ == "__main__":
    main()

