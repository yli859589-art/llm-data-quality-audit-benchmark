from __future__ import annotations

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _release_copy(tmp_path: Path) -> Path:
    target = tmp_path / "release-copy"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(".git", "dist", "test_tmp", "__pycache__", "*.pyc"),
    )
    return target


def test_claim_checker_repeated_run_is_idempotent(tmp_path: Path) -> None:
    release_root = _release_copy(tmp_path)
    tracked = release_root / "artifacts/localmax_release/reports/localmax_release_claim_check.json"
    subprocess.run(
        [sys.executable, "scripts/localmax/check_localmax_release_claims.py"],
        cwd=release_root,
        check=True,
    )
    middle = _hash(tracked)
    subprocess.run(
        [sys.executable, "scripts/localmax/check_localmax_release_claims.py"],
        cwd=release_root,
        check=True,
    )
    after = _hash(tracked)
    assert middle == after


def test_release_finalizer_repeated_run_is_idempotent(tmp_path: Path) -> None:
    release_root = _release_copy(tmp_path)
    tracked = release_root / "artifacts/localmax_release/localmax_artifact_registry.jsonl"
    subprocess.run(
        [sys.executable, "scripts/localmax/finalize_localmax_release.py"],
        cwd=release_root,
        check=True,
    )
    before = _hash(tracked)
    subprocess.run(
        [sys.executable, "scripts/localmax/finalize_localmax_release.py"],
        cwd=release_root,
        check=True,
    )
    after = _hash(tracked)
    assert before == after
