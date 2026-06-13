from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_claim_checker_repeated_run_is_idempotent() -> None:
    tracked = ROOT / "artifacts/localmax_release/reports/localmax_release_claim_check.json"
    before = _hash(tracked)
    subprocess.run([sys.executable, "scripts/localmax/check_localmax_release_claims.py"], cwd=ROOT, check=True)
    middle = _hash(tracked)
    subprocess.run([sys.executable, "scripts/localmax/check_localmax_release_claims.py"], cwd=ROOT, check=True)
    after = _hash(tracked)
    assert before == middle == after


def test_release_finalizer_repeated_run_is_idempotent() -> None:
    tracked = ROOT / "artifacts/localmax_release/localmax_artifact_registry.jsonl"
    subprocess.run([sys.executable, "scripts/localmax/finalize_localmax_release.py"], cwd=ROOT, check=True)
    before = _hash(tracked)
    subprocess.run([sys.executable, "scripts/localmax/finalize_localmax_release.py"], cwd=ROOT, check=True)
    after = _hash(tracked)
    assert before == after

