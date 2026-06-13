from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "scripts"))
import run_all_checks as rac  # noqa: E402


def test_run_all_checks_lists_required_step9_hotfix_groups() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_all_checks.py", "--list-groups"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    groups = set(result.stdout.splitlines())

    assert "legacy_core_tests" in groups
    assert "step9_readiness_tests" in groups
    assert "manifest_checks" in groups
    assert "artifact_checks" in groups
    assert "claim_checks" in groups
    assert "level3_gate_checks" in groups


def test_run_all_checks_failed_group_is_not_overall_passed() -> None:
    group = rac.CheckGroup(
        "synthetic_failure",
        [rac.CheckCommand([sys.executable, "-c", "import sys; sys.exit(7)"])],
    )

    result = rac._run_group(group, timeout=30)

    assert result.status == "failed"
    assert rac._overall_status([result]) == "failed"


def test_run_all_checks_timeout_group_is_not_overall_passed() -> None:
    group = rac.CheckGroup(
        "synthetic_timeout",
        [rac.CheckCommand([sys.executable, "-c", "import time; time.sleep(5)"])],
    )

    result = rac._run_group(group, timeout=1)

    assert result.status == "timeout"
    assert rac._overall_status([result]) == "timeout"
