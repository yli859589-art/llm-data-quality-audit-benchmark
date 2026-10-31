from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()
EXPECTED_HASHES = {
    "artifacts/tables/main_results.csv": "D8E593744EEB95CECB422C600CEC89C70279B28E09FCD3DE96AA8D1C9F2A7C3F",
    "artifacts/stats/main_results.csv": "38AA59CE82B2511FBF711D4B696E7B47C7C89F94D2ABCA0835D75AC0F14057B4",
    "artifacts/cross_dataset/cross_dataset_results.csv": "5003F1534231EEDAEE6B501D6F9769C45CEF749CFE37921E8AB10CCE12C73A86",
    "artifacts/runs/run_registry.jsonl": "D9EF6C857EC44CEF1659F1444752C6B4FC2C86C443F27665621CEA39B45086D8",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest().upper()


def test_step10a_hotfix_does_not_modify_protected_result_files() -> None:
    for relative_path, expected in EXPECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected


def test_step10a_hotfix_readiness_fields_are_boundary_preserving() -> None:
    subprocess.run(
        [sys.executable, "scripts/write_step10A_readiness_report.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    report = json.loads(
        (ROOT / "artifacts/reports/step10A_readiness_report.json").read_text(encoding="utf-8")
    )

    assert report["step10A_hotfix_applied"] is True
    assert report["artifact_scanner_path_independence_fixed"] is True
    assert report["artifact_registry_finalized_after_reports"] is True
    assert report["artifact_registry_hash_check_passed_after_finalization"] is True
    assert report["registry_check_order_hardened"] is True
    assert report["current_readiness"] == "LEVEL3_PIPELINE_READY"
    assert report["heavy_execution_completed"] is False
    assert report["level3_completed_artifact"] is False
    assert report["main_results_modified"] is False
