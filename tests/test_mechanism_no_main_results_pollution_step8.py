from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path


PROTECTED_RESULTS = [
    Path("artifacts/tables/main_results.csv"),
    Path("artifacts/stats/main_results.csv"),
    Path("artifacts/cross_dataset/cross_dataset_results.csv"),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_mechanism_manifest_check_does_not_modify_main_results() -> None:
    before = {path.as_posix(): _sha256(path) for path in PROTECTED_RESULTS}

    subprocess.run(
        [sys.executable, "scripts/check_mechanism_manifests.py", "--include-step8"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )

    after = {path.as_posix(): _sha256(path) for path in PROTECTED_RESULTS}
    assert after == before

