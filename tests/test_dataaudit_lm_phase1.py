from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from dataaudit_lm.registry.metadata import collect_evidence_summary

ROOT = Path.cwd()


def test_dataaudit_lm_summary_reads_existing_evidence() -> None:
    summary = collect_evidence_summary()

    assert summary.dataset_count == 2
    assert summary.method_count == 7
    assert summary.seed_count == 3
    assert summary.completed_runs == 42
    assert summary.tokens_per_run >= 5_000_000
    assert summary.final_gate_passed is False


def test_metric_audit_entrypoint_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dataaudit_lm/audit_metric_correctness.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["metric_audit_passed"] is True


def test_release_finalizer_does_not_promote_unfinished_matrix() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dataaudit_lm/finalize_release.py", "--audit-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["final_release_gate_passed"] is False
    assert payload["message"] == "AUDIT_COMPLETED_RELEASE_NOT_READY"

    report = json.loads(
        (ROOT / "artifacts/dataaudit_lm/reports/final_release_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["evidence"]["completed_runs"] == 42
    assert report["evidence"]["target_runs"] >= 60
