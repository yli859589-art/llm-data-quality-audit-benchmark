from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_step10c_report_keeps_level3_and_downstream_false() -> None:
    report = json.loads((ROOT / "artifacts/reports/step10C_localmax_release_report.json").read_text(encoding="utf-8"))

    assert report["level3_completed_artifact"] is False
    assert report["ccf_b_ready_claimed"] is False
    assert report["weak_ccf_a_claimed"] is False
    assert report["urd_beats_raw_claimed"] is False
    assert report["ppl_improvement_claimed"] is False
    assert report["official_downstream_completed"] is False
    assert report["true_medium_completed"] is False
    assert report["large_lite_completed"] is False
    assert report["recommended_next_step"] == "optional_cloud_level3_execution"


def test_localmax_results_doc_preserves_mixed_urd_disclosure() -> None:
    text = (ROOT / "docs/LOCALMAX_RESULTS.md").read_text(encoding="utf-8")

    assert "URD-fixed evidence is mixed" in text
    assert "does not support a claim that URD-fixed outperforms raw" in text
    assert "PPL status: clipped" in text

