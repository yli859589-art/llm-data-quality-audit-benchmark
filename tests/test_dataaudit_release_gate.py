from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()


def test_audit_only_returns_zero_when_matrix_unfinished() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dataaudit_lm/finalize_release.py", "--audit-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["final_release_gate_passed"] is False
    assert payload["message"] == "AUDIT_COMPLETED_RELEASE_NOT_READY"


def test_release_returns_nonzero_when_matrix_unfinished() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dataaudit_lm/finalize_release.py", "--release"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "RELEASE_GATE_FAILED" in result.stdout


def test_mock_release_gate_pass_requires_test_guard() -> None:
    env = os.environ.copy()
    env["DATAAUDIT_LM_ALLOW_TEST_RELEASE"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/dataaudit_lm/finalize_release.py",
            "--release",
            "--test-only-force-gates-pass",
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["final_release_gate_passed"] is True
    assert payload["message"] == "RELEASE_GATE_PASSED"
