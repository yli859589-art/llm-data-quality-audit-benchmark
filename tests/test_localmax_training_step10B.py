from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_training_writes_real_small_metrics_without_medium_claims() -> None:
    small = json.loads((ROOT / "artifacts/reports/localmax_small_training_report.json").read_text(encoding="utf-8"))
    medium = json.loads((ROOT / "artifacts/reports/localmax_medium_lite_training_report.json").read_text(encoding="utf-8"))

    assert small["localmax_small_training_ready"] is True
    assert small["completed_real_training_runs"] == small["expected_training_runs"]
    assert small["completed_real_training_runs"] >= 24
    first = small["training_results"][0]
    metrics = json.loads((ROOT / first["metrics_path"]).read_text(encoding="utf-8"))
    assert metrics["completed"] is True
    assert metrics["tokens_seen"] > 0
    assert medium["medium_lite_completed"] is False
    assert medium["true_medium_completed"] is False
    assert medium["large_lite_completed"] is False
