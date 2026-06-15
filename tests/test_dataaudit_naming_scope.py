from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()


def test_new_dataaudit_mainline_has_no_legacy_naming_hits() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dataaudit_lm/generate_naming_inventory.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["new_scope_hit_count"] == 0
    report = json.loads(
        (ROOT / "artifacts/dataaudit_lm/reports/naming_inventory.json").read_text(encoding="utf-8")
    )
    assert report["full_repo_zero_hit_required_this_round"] is False
