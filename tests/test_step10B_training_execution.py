from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def _load(name: str) -> dict:
    return json.loads((ROOT / "artifacts/reports" / name).read_text(encoding="utf-8"))


def test_step10b_small_only_does_not_pass_model_scale_gate() -> None:
    small = _load("step10B_small_training_report.json")
    medium = _load("step10B_medium_training_report.json")
    large = _load("step10B_large_lite_report.json")

    assert small["level3_small_training_ready"] is False
    assert medium["level3_medium_training_ready"] is False
    assert large["level3_large_lite_ready"] is False
    assert medium["completed"] is False
    assert large["level3_completed_artifact"] is False

