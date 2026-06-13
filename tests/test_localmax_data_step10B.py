from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_data_report_counts_real_gpt2_tokens_without_promoting_to_level3() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_data_report.json").read_text(encoding="utf-8"))

    assert report["tokenizer_name"] == "gpt2"
    assert report["token_counter_type"] == "gpt2_bpe"
    assert report["localmax_data_ready"] is True
    assert report["datasets_meeting_20m_floor"] >= 2
    assert report["level3_data_ready"] is False
    assert all(row["fallback_used"] is False for row in report["nontrivial_datasets"])
    assert all(row["actual_gpt2_tokens"] >= 20_000_000 for row in report["nontrivial_datasets"])


def test_localmax_data_manifests_are_written() -> None:
    for dataset_id in ["openwebtext_20m", "c4_en_20m"]:
        manifest = ROOT / "artifacts/localmax_data" / dataset_id / "data_manifest.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        assert payload["token_counter_type"] == "gpt2_bpe"
        assert payload["actual_gpt2_tokens"] >= 20_000_000
        assert payload["level3_data"] is False
