from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_training_completed_24_runs_at_1m_tokens() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_v2_training_report.json").read_text(encoding="utf-8"))
    assert report["localmax_v2_training_ready"] is True
    assert report["completed_core_runs"] == 24
    assert report["expected_core_runs"] == 24
    assert report["min_tokens_seen_per_completed_run"] >= 1_000_000
    assert report["total_training_tokens_seen"] >= 24_000_000
    assert report["model_scale"] == "small"
    assert report["context_length"] == 256
    for row in report["training_results"]:
        assert row["completed"] is True
        metrics = json.loads((ROOT / row["metrics_path"]).read_text(encoding="utf-8"))
        assert metrics["tokens_seen"] >= 1_000_000
        assert metrics["metric_audit_passed"] is True
        assert metrics["valid_nll_nats_per_token"] == metrics["valid_loss"]
