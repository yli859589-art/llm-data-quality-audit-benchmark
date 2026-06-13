from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from artifacts_v2.scanner import scan_artifacts
from artifacts_v2.table_linker import MAIN_TABLES, smoke_or_protocol_in_main_tables
from artifacts_v2.validation import validate_registry_rows
from readiness_v2.gates import scan_forbidden_claims
from readiness_v2.states import ReadinessState
from readiness_v2.validator import validate_level3_readiness


ROOT = Path.cwd()


def _load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_level3_readiness_is_pipeline_ready_but_not_completed() -> None:
    report = validate_level3_readiness(ROOT)

    assert report["current_readiness"] == ReadinessState.LEVEL3_PIPELINE_READY.value
    assert report["level3_completed_artifact"] is False
    assert report["heavy_execution_completed"] is False
    assert report["gates"]["claim_gate"]["status"] == "pass"
    assert report["gates"]["data_gate"]["status"] == "not_ready"


def test_level3_forbidden_claim_scanner_allows_boundary_contexts_only() -> None:
    assert scan_forbidden_claims(ROOT) == []


def test_claim_map_keeps_level3_claims_future_only() -> None:
    claim_map = _load_json("artifacts/claim_map/claim_map_level3.json")

    assert claim_map["current_readiness"] == ReadinessState.LEVEL3_PIPELINE_READY.value
    assert claim_map["level3_completed_artifact"] is False
    assert "future_level3_claims" in claim_map
    assert any("Level 3 completed" in item for item in claim_map["disallowed_current_claims"])


def test_artifact_scanner_registers_historical_main_tables_without_level3_evidence() -> None:
    records = [record.to_dict() for record in scan_artifacts(ROOT)]
    by_path = {record["path"]: record for record in records}

    for table in MAIN_TABLES:
        assert table in by_path
        assert by_path[table]["artifact_type"] == "main_table"
        assert by_path[table]["main_evidence"] is True
        assert by_path[table]["level3_evidence"] is False
        assert by_path[table]["evidence_level"] == "historical_main_only"
        assert by_path[table]["notes"] == "historical_legacy=true"

    assert validate_registry_rows(records, ROOT) == []


def test_main_tables_do_not_contain_smoke_or_protocol_artifact_paths() -> None:
    assert smoke_or_protocol_in_main_tables(ROOT) == []


def test_protocol_artifacts_are_not_marked_completed() -> None:
    offenders = []
    for path in sorted((ROOT / "artifacts").glob("**/*.json")):
        payload = _load_json(path.relative_to(ROOT).as_posix())
        if not isinstance(payload, dict):
            continue
        if payload.get("protocol_only") is True and payload.get("completed") is True:
            offenders.append(path.relative_to(ROOT).as_posix())
        if "downstream_protocol" in path.as_posix().casefold() and payload.get("completed") is True:
            offenders.append(path.relative_to(ROOT).as_posix())

    assert offenders == []


def test_run_all_checks_exposes_level3_groups() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_all_checks.py", "--list-groups"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )

    groups = set(result.stdout.splitlines())
    assert "level3_gate_checks" in groups
    assert "artifact_checks" in groups
    assert "claim_checks" in groups


def test_step5_and_step6_debt_fields_are_present() -> None:
    step5 = _load_json("artifacts/reports/step5_readiness_report.json")
    assert step5["resume_supported"] is False
    assert step5["independent_eval_split_supported"] is False

    registry_lines = (ROOT / "artifacts/training_step5/training_registry.jsonl").read_text(encoding="utf-8").splitlines()
    rows = [json.loads(line) for line in registry_lines if line.strip()]
    assert rows
    assert all(row.get("run_id") for row in rows)
    assert all(row.get("manifest_hash") for row in rows)

    for manifest_path in sorted((ROOT / "artifacts/filter_outputs_step6").glob("**/filter_manifest.json")):
        payload = _load_json(manifest_path.relative_to(ROOT).as_posix())
        if payload.get("method_family") == "URD-Selector":
            assert payload["urd_extension_version"] == "step6.urd_manifest.v1"
            assert "ablation_evaluation_scope" in payload
