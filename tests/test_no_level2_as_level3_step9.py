from __future__ import annotations

import json
from pathlib import Path

from readiness_v2.validator import validate_level3_readiness


ROOT = Path.cwd()


def test_current_reports_do_not_mark_level3_completed_artifact() -> None:
    report = validate_level3_readiness(ROOT)
    assert report["level3_completed_artifact"] is False

    offenders = []
    for path in sorted((ROOT / "artifacts/reports").glob("*readiness_report.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("level3_completed_artifact") is True:
            offenders.append(path.relative_to(ROOT).as_posix())
        if payload.get("current_readiness") == "LEVEL3_COMPLETED_ARTIFACT":
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []


def test_step9_report_keeps_pipeline_ready_distinct_from_completed() -> None:
    payload = json.loads((ROOT / "artifacts/reports/step9_readiness_report.json").read_text(encoding="utf-8"))

    assert payload["current_readiness"] == "LEVEL3_PIPELINE_READY"
    assert payload["level3_completed_artifact"] is False
    assert payload["heavy_execution_completed"] is False
