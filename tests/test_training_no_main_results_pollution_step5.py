from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

from training_v2.validation import assert_training_outputs_not_in_main_results


PROTECTED_RESULTS = [
    Path("artifacts/tables/main_results.csv"),
    Path("artifacts/stats/main_results.csv"),
    Path("artifacts/cross_dataset/cross_dataset_results.csv"),
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_step5_training_outputs_do_not_pollute_main_results() -> None:
    before = {path.as_posix(): _sha256(path) for path in PROTECTED_RESULTS}

    assert_training_outputs_not_in_main_results(Path.cwd())
    subprocess.run(
        [sys.executable, "scripts/check_training_manifests.py", "--include-step5"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )

    after = {path.as_posix(): _sha256(path) for path in PROTECTED_RESULTS}
    assert after == before
