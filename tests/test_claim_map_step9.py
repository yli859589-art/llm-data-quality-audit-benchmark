from __future__ import annotations

import json
from pathlib import Path


ROOT = Path.cwd()


def test_claim_map_keeps_level3_and_ccf_claims_bounded() -> None:
    claim_map = json.loads((ROOT / "artifacts/claim_map/claim_map_level3.json").read_text(encoding="utf-8"))

    assert claim_map["current_readiness"] == "LEVEL3_PIPELINE_READY"
    assert claim_map["level3_completed_artifact"] is False
    assert "ccf_level_claims" in claim_map
    assert "Level 3 completed." in claim_map["ccf_level_claims"]["disallowed_current"]
    assert "CCF-B ready." in claim_map["ccf_level_claims"]["disallowed_current"]


def test_claim_map_disallows_current_urd_effectiveness_claims() -> None:
    claim_map = json.loads((ROOT / "artifacts/claim_map/claim_map_level3.json").read_text(encoding="utf-8"))

    disallowed = " ".join(claim_map["urd_claims"]["disallowed_current"])
    assert "URD beats raw" in disallowed
    assert "URD improves PPL" in disallowed
    assert "URD improves downstream" in disallowed
