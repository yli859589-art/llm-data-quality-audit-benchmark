from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path.cwd()


def test_step10A_claim_map_records_protocol_only_boundary() -> None:
    claim_map = json.loads((ROOT / "artifacts/claim_map/claim_map_level3.json").read_text(encoding="utf-8"))

    assert claim_map["current_readiness"] == "LEVEL3_PIPELINE_READY"
    assert claim_map["level3_completed_artifact"] is False
    assert claim_map["level3_heavy_protocol_frozen"] is True
    assert claim_map["step10A_protocol_only"] is True
    assert claim_map["step10A_heavy_execution_completed"] is False
    assert any("Step 10A freezes" in claim for claim in claim_map["allowed_current_claims"])
    assert "Step 10B heavy execution completed." in claim_map["disallowed_current_claims"]


def test_public_claim_checks_still_pass_after_step10A_docs() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/check_no_forbidden_claims.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    assert "Forbidden claim check: ok" in result.stdout

