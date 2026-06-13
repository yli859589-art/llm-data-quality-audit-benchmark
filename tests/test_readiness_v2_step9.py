from __future__ import annotations

import json
from pathlib import Path

from readiness_v2.states import ORDERED_STATES, ReadinessState
from readiness_v2.validator import validate_level3_readiness


ROOT = Path.cwd()


def test_readiness_states_include_level3_route_and_completion_boundary() -> None:
    expected = {
        "EXPERIMENT_CANDIDATE",
        "LEVEL3_PIPELINE_READY",
        "LEVEL3_DATA_READY",
        "LEVEL3_FILTERS_READY",
        "LEVEL3_TRAINING_PARTIAL",
        "LEVEL3_TRAINING_READY",
        "LEVEL3_EVALUATION_PARTIAL",
        "LEVEL3_EVALUATION_READY",
        "LEVEL3_MECHANISM_READY",
        "LEVEL3_COMPLETED_ARTIFACT",
    }
    assert expected.issubset(set(ORDERED_STATES))


def test_current_readiness_does_not_return_completed_without_heavy_execution() -> None:
    report = validate_level3_readiness(ROOT)

    assert report["current_readiness"] == ReadinessState.LEVEL3_PIPELINE_READY.value
    assert report["current_readiness"] != ReadinessState.LEVEL3_COMPLETED_ARTIFACT.value
    assert report["level3_completed_artifact"] is False
    assert report["heavy_execution_completed"] is False


def test_step9_readiness_report_contains_required_gate_and_debt_fields() -> None:
    report = json.loads((ROOT / "artifacts/reports/step9_readiness_report.json").read_text(encoding="utf-8"))

    required = {
        "step",
        "status",
        "tests_passed",
        "run_all_checks_passed",
        "artifact_registry_v2_passed",
        "claim_map_passed",
        "claim_hygiene_passed",
        "registry_to_tables_passed",
        "main_results_from_registry_passed",
        "level3_gates_checked",
        "data_gate",
        "tokenizer_gate",
        "filter_gate",
        "model_scale_gate",
        "evaluation_gate",
        "mechanism_gate",
        "claim_gate",
        "current_readiness",
        "level3_completed_artifact",
        "heavy_execution_completed",
        "technical_debt_fixed",
        "technical_debt_remaining",
    }
    assert required.issubset(report)
    assert report["level3_completed_artifact"] is False
    assert report["heavy_execution_completed"] is False
    assert "run_all_checks_grouped_execution" in report["technical_debt_fixed"]
