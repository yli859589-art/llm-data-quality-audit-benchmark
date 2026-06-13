from __future__ import annotations

import json
from pathlib import Path

from artifacts_v2.scanner import scan_artifacts


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _steps_by_path(root: Path) -> dict[str, str]:
    return {record.path: record.step for record in scan_artifacts(root)}


def test_scanner_uses_repo_relative_path_when_parent_contains_step10a(tmp_path: Path) -> None:
    root = tmp_path / "parent_step10a_audit" / "repo"
    _write_json(root / "artifacts/filter_outputs_step4/example/filter_manifest.json", {"filter_name": "raw"})
    _write_json(root / "artifacts/reports/step10A_readiness_report.json", {"protocol_only": True, "completed": False})

    steps = _steps_by_path(root)

    assert steps["artifacts/filter_outputs_step4/example/filter_manifest.json"] == "step4"
    assert steps["artifacts/reports/step10A_readiness_report.json"] == "step10A"


def test_scanner_uses_repo_relative_path_when_parent_contains_step1(tmp_path: Path) -> None:
    root = tmp_path / "parent_step1_review" / "repo"
    _write_json(root / "artifacts/evaluation_step7/example/evaluation_manifest.json", {"evaluation_type": "lm"})
    _write_json(root / "artifacts/analysis_step8/example/mechanism_manifest.json", {"analysis_type": "domain_shift"})

    steps = _steps_by_path(root)

    assert steps["artifacts/evaluation_step7/example/evaluation_manifest.json"] == "step7"
    assert steps["artifacts/analysis_step8/example/mechanism_manifest.json"] == "step8"


def test_step10a_is_not_misclassified_as_step1_in_current_repo() -> None:
    root = Path.cwd()
    records = {record.path: record.step for record in scan_artifacts(root)}

    assert records["artifacts/reports/step10A_readiness_report.json"] == "step10A"

