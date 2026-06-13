from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_claim_boundary_does_not_overclaim() -> None:
    release = json.loads((ROOT / "artifacts/reports/step10C_localmax_v2_release_report.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "artifacts/localmax_v2_release/localmax_v2_release_manifest.json").read_text(encoding="utf-8"))
    assert release["current_readiness"] == "LOCAL_MAX_V2_STRONG_EVIDENCE_RELEASED"
    for payload in [release, manifest]:
        assert payload["level3_completed_artifact"] is False
        assert payload["ccf_b_ready_claimed"] is False
        assert payload["weak_ccf_a_claimed"] is False
        assert payload["sota_claimed"] is False
    claim_doc = (ROOT / "docs/LOCALMAX_V2_CLAIM_BOUNDARY.md").read_text(encoding="utf-8")
    assert "URD beats raw unless" in claim_doc
    assert "CCF-B ready" in claim_doc
