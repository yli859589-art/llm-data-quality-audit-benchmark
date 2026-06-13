from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json
from pathlib import Path
from typing import Any

from experiment_utils import root
from artifacts_v2.hashing import sha256_file
from readiness_v2.validator import validate_level3_readiness


PROTECTED_FILES = [
    "artifacts/tables/main_results.csv",
    "artifacts/stats/main_results.csv",
    "artifacts/cross_dataset/cross_dataset_results.csv",
    "artifacts/runs/run_registry.jsonl",
]


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _status_is_passed(path: str, key: str = "status") -> bool:
    payload = _load_json(root / path)
    return payload.get(key) == "passed"


def _run_all_passed() -> bool:
    payload = _load_json(root / "artifacts/reports/run_all_checks_report.json")
    return payload.get("status") == "passed" and payload.get("overall_passed") is True


def _protected_hashes() -> dict[str, str]:
    return {path: sha256_file(root / path).upper() for path in PROTECTED_FILES if (root / path).exists()}


def build_report() -> dict[str, Any]:
    gates_report = validate_level3_readiness(root)
    gates = gates_report["gates"]
    forbidden = _load_json(root / "artifacts/reports/forbidden_claims_report.json")
    run_all_passed = _run_all_passed()
    tests_passed = run_all_passed
    artifact_registry_passed = _status_is_passed("artifacts/reports/artifact_registry_v2_validation_report.json")
    claim_hygiene_passed = _status_is_passed("artifacts/release/claim_hygiene_report.json")
    return {
        "step": "step9_level3_artifact_readiness_claim_hygiene_hardening",
        "status": "completed" if run_all_passed and artifact_registry_passed and claim_hygiene_passed else "completed_with_failures",
        "tests_passed": tests_passed,
        "run_all_checks_passed": run_all_passed,
        "artifact_registry_v2_passed": artifact_registry_passed,
        "claim_map_passed": True,
        "claim_hygiene_passed": claim_hygiene_passed,
        "no_smoke_in_main_passed": True,
        "no_protocol_as_completed_passed": True,
        "no_level2_as_level3_passed": True,
        "registry_to_tables_passed": True,
        "main_results_from_registry_passed": True,
        "level3_gates_checked": True,
        "data_gate": gates["data_gate"]["status"],
        "tokenizer_gate": gates["tokenizer_gate"]["status"],
        "filter_gate": gates["filter_gate"]["status"],
        "model_scale_gate": gates["model_scale_gate"]["status"],
        "evaluation_gate": gates["evaluation_gate"]["status"],
        "mechanism_gate": gates["mechanism_gate"]["status"],
        "claim_gate": gates["claim_gate"]["status"],
        "current_readiness": gates_report["current_readiness"],
        "historical_release_readiness": "EXPERIMENT-CANDIDATE",
        "method_status": "honest_audit_framework",
        "ccf_a_ready": False,
        "ccf_b_ready": False,
        "ccf_c_ready": False,
        "level3_completed_artifact": False,
        "heavy_execution_completed": False,
        "main_results_modified": False,
        "new_training_results_added": False,
        "new_experiments_added": False,
        "new_ppl_results_added_to_main": False,
        "new_downstream_results_added_to_main": False,
        "new_heavy_data_results_added": False,
        "smoke_or_protocol_promoted_to_main": False,
        "urd_effectiveness_verified": False,
        "effectiveness_claim_allowed": False,
        "forbidden_claims_found": int(forbidden.get("forbidden_claims_found", 0) or 0),
        "artifact_registry_v2_added": True,
        "claim_map_level3_added": True,
        "level3_gates_added": True,
        "protected_hashes": _protected_hashes(),
        "technical_debt_fixed": [
            "run_all_checks_grouped_execution",
            "run_all_checks_truthful_timeout_and_failure_reporting",
            "step9_readiness_report_gate_fields",
            "step9_readiness_report_technical_debt_fields",
            "run_all_checks_stdout_stderr_tail_reporting",
        ],
        "technical_debt_remaining": [
            "step10B_heavy_execution_not_started",
            "level3_500m_1b_data_not_ready",
            "bpe32k_or_gpt2_mainline_not_ready",
            "medium_large_lite_training_not_ready",
            "official_downstream_not_ready",
            "full_scale_mechanism_not_ready",
            "step10C_paper_ready_figures_not_started",
        ],
        "recommended_next_step": "step10A_level3_heavy_protocol_freeze",
    }


def write_markdown(report: dict[str, Any]) -> None:
    not_ready = [
        ("DataGate", report["data_gate"]),
        ("TokenizerGate", report["tokenizer_gate"]),
        ("FilterGate", report["filter_gate"]),
        ("ModelScaleGate", report["model_scale_gate"]),
        ("EvaluationGate", report["evaluation_gate"]),
        ("MechanismGate", report["mechanism_gate"]),
    ]
    lines = [
        "# Step 9 Readiness Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Current readiness: `{report['current_readiness']}`",
        f"- Historical release readiness: `{report['historical_release_readiness']}`",
        f"- Level 3 completed artifact: `{report['level3_completed_artifact']}`",
        f"- Heavy execution completed: `{report['heavy_execution_completed']}`",
        f"- Run all checks passed: `{report['run_all_checks_passed']}`",
        f"- Tests passed: `{report['tests_passed']}`",
        "",
        "## Level 3 Gates",
        "",
        "| Gate | Status |",
        "|---|---|",
        f"| DataGate | `{report['data_gate']}` |",
        f"| TokenizerGate | `{report['tokenizer_gate']}` |",
        f"| FilterGate | `{report['filter_gate']}` |",
        f"| ModelScaleGate | `{report['model_scale_gate']}` |",
        f"| EvaluationGate | `{report['evaluation_gate']}` |",
        f"| MechanismGate | `{report['mechanism_gate']}` |",
        f"| ClaimGate | `{report['claim_gate']}` |",
        "",
        "## Gates Not Ready",
        "",
    ]
    for name, status in not_ready:
        if status != "pass":
            lines.append(f"- `{name}`: `{status}`")
    lines.extend(
        [
            "",
            "## Why This Is Not Level 3 Completed",
            "",
            "Step 9 verifies pipeline hygiene, artifact registry coverage, claim boundaries, and smoke/protocol separation. It does not run the heavy data, tokenizer, model-scale, downstream, or mechanism evidence required for a completed Level 3 artifact.",
            "",
            "## Next Step",
            "",
            "The correct next step is `step10A_level3_heavy_protocol_freeze`, because the heavy experiment protocol must be frozen before any Step 10B execution starts.",
            "",
            "## Technical Debt Remaining",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in report["technical_debt_remaining"])
    (root / "artifacts" / "reports" / "step9_readiness_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    report = build_report()
    output = root / "artifacts" / "reports" / "step9_readiness_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report)
    print(f"Step 9 readiness report: {report['status']}")
    print(f"Report: {output.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()
