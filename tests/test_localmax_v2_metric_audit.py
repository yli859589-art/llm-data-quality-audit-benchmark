from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_localmax_v2_metric_audit_canaries_pass() -> None:
    report = json.loads((ROOT / "artifacts/reports/localmax_v2_metric_audit.json").read_text(encoding="utf-8"))
    canary = report["canary_tests"]
    assert report["metric_audit_passed"] is True
    assert abs(canary["uniform_logits_loss"] - math.log(50257)) < 1e-4
    assert canary["perfect_prediction_loss"] < 1e-4
    assert canary["shift_input"] == [[10, 11, 12]]
    assert canary["shift_labels"] == [[11, 12, 13]]
    assert report["ppl_policy"]["clipping_allowed_for_ranking"] is False
