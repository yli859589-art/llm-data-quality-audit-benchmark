from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()


def _run(script: str) -> dict:
    result = subprocess.run(
        [sys.executable, script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    return json.loads(result.stdout)


def test_level3_dryrun_scripts_emit_plans_without_execution() -> None:
    scripts = [
        "scripts/level3/prepare_level3_data_plan.py",
        "scripts/level3/run_level3_filters_plan.py",
        "scripts/level3/run_level3_training_plan.py",
        "scripts/level3/run_level3_evaluation_plan.py",
        "scripts/level3/run_level3_analysis_plan.py",
        "scripts/level3/release_level3_plan.py",
    ]

    for script in scripts:
        payload = _run(script)
        assert payload["step"] == "step10A_level3_heavy_protocol_freeze"
        assert payload["dry_run"] is True
        assert payload["protocol_only"] is True
        assert payload["completed"] is False
        assert payload["executed"] is False
        assert payload["planned_commands"]
        assert payload["expected_artifacts"]
        assert payload["required_resources"]
        assert "not executed" in payload["not_executed_reason"].lower()


def test_level3_dryrun_scripts_block_execute_flag_in_step10A() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/level3/prepare_level3_data_plan.py", "--execute"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    payload = json.loads(result.stdout)

    assert result.returncode == 2
    assert payload["blocked"] is True
    assert "Step 10A freezes protocol only" in payload["blocked_reason"]

