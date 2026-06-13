from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_minimal_training_outputs_are_complete_and_small_only() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_small_training_report.json").read_text(encoding="utf-8"))

    assert report["completed_real_training_runs"] == 24
    for row in report["training_results"]:
        manifest = json.loads((ROOT / row["training_manifest_path"]).read_text(encoding="utf-8"))
        metrics = json.loads((ROOT / manifest["metrics_path"]).read_text(encoding="utf-8"))
        checkpoint = json.loads((ROOT / manifest["checkpoint_manifest_path"]).read_text(encoding="utf-8"))
        assert manifest["completed"] is True
        assert manifest["model_scale"] == "small"
        assert manifest["true_medium_completed"] is False
        assert manifest["large_lite_completed"] is False
        assert metrics["tokens_seen"] > 0
        assert checkpoint["not_a_fake_checkpoint"] is True

