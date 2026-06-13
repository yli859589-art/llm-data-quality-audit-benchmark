from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path.cwd()


def test_localmax_claim_map_blocks_unsupported_claims() -> None:
    claim_map = json.loads((ROOT / "artifacts/claim_map/claim_map_localmax.json").read_text(encoding="utf-8"))

    assert claim_map["current_status"] == "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED"
    assert claim_map["level3_completed_artifact"] is False
    assert claim_map["ccf_b_ready_claimed"] is False
    assert claim_map["weak_ccf_a_claimed"] is False
    assert claim_map["urd_beats_raw_claim_allowed"] is False
    assert claim_map["ppl_improvement_claim_allowed"] is False
    assert claim_map["official_downstream_completed"] is False
    assert claim_map["true_medium_completed"] is False
    assert claim_map["large_lite_completed"] is False


def test_release_claim_audit_table_blocks_ppl_and_urd_claims() -> None:
    rows = list(csv.DictReader((ROOT / "artifacts/localmax_release/tables/localmax_claim_audit_release.csv").open(encoding="utf-8")))
    by_claim = {row["claim_id"]: row for row in rows}

    assert by_claim["localmax_minimal_training_evidence_released"]["allowed"] == "True"
    assert by_claim["urd_fixed_wins_over_raw"]["allowed"] == "False"
    assert by_claim["ppl_improvement"]["allowed"] == "False"
    assert by_claim["level3_completed"]["allowed"] == "False"

