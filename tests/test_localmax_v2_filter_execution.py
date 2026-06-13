from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_filter_matrix_completed_with_id_artifacts() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_v2_filter_report.json").read_text(encoding="utf-8"))
    assert report["localmax_v2_filters_ready"] is True
    assert len(report["filter_results"]) == 8
    for row in report["filter_results"]:
        manifest = json.loads((ROOT / row["filter_manifest_path"]).read_text(encoding="utf-8"))
        assert manifest["scope"] == "localmax_v2"
        assert manifest["smoke_only"] is False
        assert manifest["protocol_only"] is False
        assert manifest["selected_gpt2_tokens"] >= 1_000_000
        assert (ROOT / manifest["selected_doc_ids_path"]).exists()
        assert (ROOT / manifest["scores_or_decisions_path"]).exists()
