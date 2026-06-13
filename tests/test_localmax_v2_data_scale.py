from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_two_localmax_v2_datasets_reach_100m_gpt2_tokens_without_fallback() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_v2_data_report.json").read_text(encoding="utf-8"))
    assert report["localmax_v2_data_ready"] is True
    assert report["datasets_meeting_100m_floor"] == 2
    assert report["total_actual_gpt2_tokens"] >= 200_000_000
    for row in report["datasets"]:
        assert row["actual_gpt2_tokens"] >= 100_000_000
        assert row["fallback_used"] is False
        assert row["no_fallback_verified"] is True
        manifest = json.loads((ROOT / row["manifest_path"]).read_text(encoding="utf-8"))
        assert manifest["token_counter_type"] == "gpt2_bpe"
        assert manifest["split_integrity_passed"] is True
