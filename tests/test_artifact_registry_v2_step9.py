from __future__ import annotations

from pathlib import Path

from artifacts_v2.scanner import scan_artifacts
from artifacts_v2.validation import validate_registry_rows


ROOT = Path.cwd()


def test_artifact_registry_scans_step2_through_step9_artifacts() -> None:
    records = [record.to_dict() for record in scan_artifacts(ROOT)]
    types = {record["artifact_type"] for record in records}
    steps = {record["step"] for record in records}

    assert {"dataset_manifest", "filter_manifest", "training_manifest", "evaluation_manifest", "mechanism_manifest"}.issubset(types)
    assert {"step2", "step3", "step4", "step5", "step6", "step7", "step8", "step9"}.issubset(steps)
    assert validate_registry_rows(records, ROOT) == []


def test_registry_never_marks_smoke_or_protocol_as_main_evidence() -> None:
    records = [record.to_dict() for record in scan_artifacts(ROOT)]

    offenders = [
        record["path"]
        for record in records
        if (record["smoke_only"] or record["protocol_only"]) and record["main_evidence"]
    ]
    assert offenders == []
