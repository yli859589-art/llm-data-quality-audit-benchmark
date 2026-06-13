from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json

from experiment_utils import root
from level3.protocol_utils import protected_hashes, utc_now, validate_protocol, write_report


def build_preflight_report() -> dict:
    protocol = validate_protocol()
    protocol_passed = protocol["status"] == "passed"
    return {
        "step": "step10A_level3_heavy_protocol_freeze",
        "status": "passed" if protocol_passed else "failed",
        "checked_at": utc_now(),
        "protocol_only": True,
        "completed": False,
        "current_readiness": "LEVEL3_PIPELINE_READY",
        "level3_completed_artifact": False,
        "heavy_execution_completed": False,
        "heavy_execution_ready": False,
        "data_ready": False,
        "tokenizer_mainline_ready": False,
        "filter_matrix_ready": False,
        "training_ready": False,
        "evaluation_ready": False,
        "mechanism_ready": False,
        "claim_boundary_ready": protocol_passed,
        "safe_to_start_step10B_only_after_resource_confirmation": protocol_passed,
        "blocking_items_for_completed_level3": [
            "prepare at least three 500M-token no-fallback BPE-counted datasets",
            "train or lock GPT-2/BPE16k/BPE32k mainline tokenizers with manifests",
            "run full baseline/filter matrix under matched keep-rate",
            "run small and medium models with multi-seed protocol",
            "run selected large-lite evidence with explicit exploratory label",
            "complete official downstream and mechanism-analysis evidence",
        ],
        "protocol_report_status": protocol["status"],
        "protocol_errors": protocol["errors"],
        "protected_hashes": protected_hashes(),
    }


def main() -> None:
    payload = build_preflight_report()
    write_report(
        payload,
        root / "artifacts" / "reports" / "level3_preflight_report.json",
        root / "artifacts" / "reports" / "level3_preflight_report.md",
        "Level 3 Preflight Report",
    )
    if payload["status"] != "passed":
        raise SystemExit("Level 3 preflight failed.\n" + json.dumps(payload, indent=2, sort_keys=True))
    print("Level 3 preflight check: ok")


if __name__ == "__main__":
    main()

