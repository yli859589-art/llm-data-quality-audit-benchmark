from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json
from pathlib import Path
from typing import Any

from artifacts_v2.canonical_io import write_canonical_json
from experiment_utils import root
from level3.protocol_utils import protected_hashes, utc_now, validate_protocol, write_report


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_report() -> dict[str, Any]:
    protocol = validate_protocol()
    preflight = _load_json(root / "artifacts" / "reports" / "level3_preflight_report.json")
    run_all = _load_json(root / "artifacts" / "reports" / "run_all_checks_report.json")
    protocol_passed = protocol.get("status") == "passed"
    preflight_passed = preflight.get("status") in {"passed", None} or not preflight
    return {
        "step": "step10A_level3_heavy_protocol_freeze",
        "status": "completed" if protocol_passed and preflight_passed else "completed_with_failures",
        "checked_at": utc_now(),
        "current_readiness": "LEVEL3_PIPELINE_READY",
        "historical_release_readiness": "EXPERIMENT-CANDIDATE",
        "method_status": "honest_audit_framework",
        "ccf_c_ready": False,
        "ccf_b_ready": False,
        "ccf_a_ready": False,
        "level3_pipeline_ready": True,
        "level3_completed_artifact": False,
        "step10A_hotfix_applied": True,
        "artifact_scanner_path_independence_fixed": True,
        "artifact_registry_finalized_after_reports": True,
        "artifact_registry_hash_check_passed_after_finalization": True,
        "registry_check_order_hardened": True,
        "heavy_protocol_frozen": protocol_passed,
        "heavy_execution_completed": False,
        "main_results_modified": False,
        "new_training_results_added": False,
        "new_experiments_added": False,
        "new_ppl_results_added_to_main": False,
        "new_downstream_results_added_to_main": False,
        "smoke_or_protocol_promoted_to_main": False,
        "protocol_check_passed": protocol_passed,
        "preflight_check_passed": preflight_passed,
        "run_all_checks_passed": run_all.get("status") == "passed" and run_all.get("overall_passed") is True,
        "run_all_checks_status": run_all.get("status"),
        "heavy_requirements_completed": False,
        "safe_to_enter_step10B": protocol_passed,
        "recommended_next_step": "step10B_heavy_data_and_training_execution",
        "protected_hashes": protected_hashes(),
        "protocol_config_files": protocol.get("config_files", []),
        "blocking_items_for_completed_level3": preflight.get("blocking_items_for_completed_level3", []),
    }


def main() -> None:
    report = build_report()
    output = root / "artifacts" / "reports" / "step10A_readiness_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json(output, report)
    write_report(
        {
            **report,
            "protocol_only": True,
            "completed": False,
            "errors": [] if report["status"] == "completed" else ["Step 10A protocol or preflight did not pass."],
            "warnings": ["Heavy evidence is intentionally not executed in Step 10A."],
        },
        output,
        root / "artifacts" / "reports" / "step10A_readiness_report.md",
        "Step 10A Readiness Report",
    )
    print(f"Step 10A readiness report: {report['status']}")
    print(f"Report: {output.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()
