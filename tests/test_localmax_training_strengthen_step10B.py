from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_strengthened_training_runs_meet_minimum_strength() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_training_strengthened_report.json").read_text(encoding="utf-8"))

    assert report["training_strengthened_completed"] is True
    assert report["completed_strengthened_runs"] == 24
    assert report["min_tokens_seen_per_completed_run"] >= 25_000
    assert report["min_steps_completed"] >= 100
    for row in report["training_results"]:
        metrics = json.loads((ROOT / row["metrics_path"]).read_text(encoding="utf-8"))
        manifest = json.loads((ROOT / row["training_manifest_path"]).read_text(encoding="utf-8"))
        assert metrics["tokens_seen"] >= 25_000
        assert metrics["steps_completed"] >= 100
        assert metrics["context_length"] >= 128
        assert metrics["validation_token_sample_cap"] >= 32_768
        assert manifest["min_training_strength_met"] is True
        assert manifest["previous_minimal_run_superseded"] is True
        assert manifest["model_scale"] == "small"
        assert manifest["true_medium_completed"] is False
        assert manifest["large_lite_completed"] is False


def test_old_minimal_two_step_runs_are_not_marked_strengthened() -> None:
    old_metrics = json.loads(
        (
            ROOT / "artifacts/localmax_training/openwebtext_20m/raw/seed_13/metrics.json"
        ).read_text(encoding="utf-8")
    )

    assert old_metrics["tokens_seen"] < 25_000
    assert old_metrics["steps_completed"] < 100

