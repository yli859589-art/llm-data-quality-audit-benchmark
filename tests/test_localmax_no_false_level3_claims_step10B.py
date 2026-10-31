from __future__ import annotations

import hashlib
import json
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


def test_localmax_does_not_modify_protected_results() -> None:
    for relative_path, expected in EXPECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected


def test_localmax_readiness_has_no_false_completion_flags() -> None:
    report = json.loads(
        (ROOT / "artifacts/reports/step10B_localmax_readiness_report.json").read_text(
            encoding="utf-8"
        )
    )
    text = (
        (ROOT / "artifacts/reports/step10B_localmax_readiness_report.md")
        .read_text(encoding="utf-8")
        .casefold()
    )

    assert report["level3_completed"] is False
    assert report["localmax_completed"] is False
    assert report["official_downstream_completed"] is False
    assert report["statistical_significance_claim_allowed"] is False
    assert "ccf-b ready" not in text
    assert "level 3 completed: `true`" not in text
