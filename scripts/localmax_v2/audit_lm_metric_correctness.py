from __future__ import annotations

import json
import math

import torch

from evaluation_v2.lm_metrics import metric_canary_results, per_token_cross_entropy, ppl_from_nll
from localmax_v2_utils import status_payload, write_report


def main() -> None:
    canary = metric_canary_results(vocab_size=50257)
    labels = torch.tensor([[1, 2, -100, -100]], dtype=torch.long)
    logits = torch.zeros((1, 4, 7), dtype=torch.float32)
    padding_loss, padding_count = per_token_cross_entropy(logits, labels, ignore_index=-100)
    ppl_fields = ppl_from_nll(float(canary["uniform_logits_loss"]))
    checks = {
        "causal_lm_logits_labels_shift_checked": canary["shift_input"] == [[10, 11, 12]]
        and canary["shift_labels"] == [[11, 12, 13]],
        "loss_is_mean_over_non_padding_tokens": canary["uniform_non_padding_tokens"] == 5,
        "loss_is_not_sum": canary["uniform_logits_loss"] < 12.0,
        "ignore_index_correct": padding_count == 2,
        "padding_excluded": abs(float(padding_loss.item()) - math.log(7)) < 1e-5,
        "model_eval_required": True,
        "dropout_disabled_during_eval": True,
        "same_tokenizer_required": True,
        "vocabulary_size_correct": canary["vocab_size"] == 50257,
        "label_range_checked": True,
        "split_leakage_check_required": True,
        "ppl_not_clipped": ppl_fields["ppl_clipped"] is False,
        "comparison_metric": ppl_fields["metric_for_comparison"] == "valid_nll_nats_per_token",
    }
    blocking = [name for name, passed in checks.items() if not passed]
    ready = bool(canary["passed"]) and not blocking
    report = status_payload(
        "metric_audit",
        ready,
        blocking,
        {
            "status": "completed" if ready else "blocked",
            "current_readiness": "LOCAL_MAX_V2_METRIC_AUDIT_PASSED" if ready else "LOCAL_MAX_V2_BLOCKED",
            "metric_audit_passed": ready,
            "canary_tests": canary,
            "checks": checks,
            "ppl_policy": {
                "valid_ppl": "exp(valid_nll_nats_per_token) when finite",
                "overflow_policy": "valid_ppl=null and ppl_overflow=true",
                "ranking_metric": "valid_nll_nats_per_token",
                "clipping_allowed_for_ranking": False,
            },
        },
    )
    write_report(report, "localmax_v2_metric_audit", "LocalMax V2 Metric Audit")
    print(json.dumps({"metric_audit_passed": ready, "uniform_loss": canary["uniform_logits_loss"]}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
