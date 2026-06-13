from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.io import write_json
from dataaudit_lm.integrity.paths import REPORTS, ensure_public_artifact_dirs
from evaluation_v2.lm_metrics import metric_canary_results, ppl_from_nll


def main() -> None:
    ensure_public_artifact_dirs()
    canary = metric_canary_results()
    ppl = ppl_from_nll(float(canary["uniform_logits_loss"]))
    checks = {
        "uniform_logits_match_log_vocab": canary["uniform_logits_abs_error"] < 1e-4,
        "perfect_prediction_near_zero": canary["perfect_prediction_loss"] < 1e-4,
        "causal_shift_checked": canary["shift_input"] == [[10, 11, 12]]
        and canary["shift_labels"] == [[11, 12, 13]],
        "padding_mask_checked": canary["padding_non_padding_tokens"] == 5,
        "ppl_identity_checked": math.isclose(
            float(ppl["valid_ppl"]),
            math.exp(float(ppl["valid_nll_nats_per_token"])),
            rel_tol=1e-12,
        ),
        "ppl_not_clipped": ppl["ppl_clipped"] is False,
    }
    passed = all(checks.values()) and bool(canary["passed"])
    payload = {
        "checks": checks,
        "metric_audit_passed": passed,
        "status": "METRIC_AUDIT_PASSED" if passed else "METRIC_AUDIT_FAILED",
    }
    write_json(REPORTS / "metric_correctness_report.json", payload)
    print(json.dumps({"metric_audit_passed": passed, "status": payload["status"]}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
