from __future__ import annotations

import json
from pathlib import Path

ROOT = Path.cwd()


def test_backup_restore_report_schema_if_present() -> None:
    path = ROOT / "artifacts/dataaudit_lm/integrity/backup_restore_report.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["bundle_exists"] is True
    assert "bundle_verify_returncode" in report
    assert "restore_successful" in report
    assert "temporary_restore_dir_cleaned" in report
