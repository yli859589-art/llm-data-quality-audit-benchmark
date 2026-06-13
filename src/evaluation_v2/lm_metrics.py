from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import torch
from torch.nn import functional as F

from .base import EvaluationConfig, EvaluationResult
from .io import read_json, resolve_path, write_json, write_text
from .manifest import create_evaluation_manifest, sha256_file, write_manifest
from .reporting import simple_report


def per_token_cross_entropy(
    logits: torch.Tensor,
    labels: torch.Tensor,
    *,
    ignore_index: int = -100,
) -> tuple[torch.Tensor, int]:
    """Return mean token NLL and the number of non-padding labels."""
    if logits.ndim != 3:
        raise ValueError("logits must have shape [batch, sequence, vocab]")
    if labels.shape != logits.shape[:2]:
        raise ValueError("labels must have shape [batch, sequence]")
    vocab_size = logits.size(-1)
    valid = labels.ne(ignore_index)
    if valid.any():
        min_label = int(labels[valid].min().item())
        max_label = int(labels[valid].max().item())
        if min_label < 0 or max_label >= vocab_size:
            raise ValueError(f"label range [{min_label}, {max_label}] is outside vocab size {vocab_size}")
    token_count = int(valid.sum().item())
    if token_count == 0:
        raise ValueError("at least one non-padding label is required")
    loss = F.cross_entropy(
        logits.reshape(-1, vocab_size),
        labels.reshape(-1),
        ignore_index=ignore_index,
        reduction="sum",
    ) / token_count
    return loss, token_count


def causal_shift_labels(input_ids: torch.Tensor, *, ignore_index: int = -100) -> tuple[torch.Tensor, torch.Tensor]:
    """Create causal LM x/y tensors with a one-token shift."""
    if input_ids.ndim != 2:
        raise ValueError("input_ids must have shape [batch, sequence]")
    if input_ids.size(1) < 2:
        raise ValueError("sequence length must be at least 2 for causal shift")
    return input_ids[:, :-1].contiguous(), input_ids[:, 1:].contiguous()


def ppl_from_nll(nll_nats_per_token: float) -> dict[str, Any]:
    """Represent PPL without clipping; use log-PPL when exp would overflow."""
    value = float(nll_nats_per_token)
    overflow = value > math.log(float("1.7976931348623157e308"))
    return {
        "valid_nll_nats_per_token": value,
        "valid_loss": value,
        "valid_log_ppl": value,
        "valid_ppl": None if overflow else math.exp(value),
        "ppl_overflow": overflow,
        "metric_for_comparison": "valid_nll_nats_per_token",
        "ppl_clipped": False,
        "ppl_comparable": not overflow,
    }


def metric_canary_results(vocab_size: int = 50257) -> dict[str, Any]:
    """Run deterministic metric canaries used by LocalMax V2."""
    labels = torch.tensor([[0, 1, 2, -100], [3, 4, -100, -100]], dtype=torch.long)
    uniform_logits = torch.zeros((*labels.shape, vocab_size), dtype=torch.float32)
    uniform_loss, uniform_count = per_token_cross_entropy(uniform_logits, labels)
    expected = math.log(vocab_size)

    perfect_labels = torch.tensor([[2, 1, 0]], dtype=torch.long)
    perfect_logits = torch.full((*perfect_labels.shape, 5), -40.0, dtype=torch.float32)
    for batch in range(perfect_labels.size(0)):
        for pos in range(perfect_labels.size(1)):
            perfect_logits[batch, pos, int(perfect_labels[batch, pos])] = 40.0
    perfect_loss, perfect_count = per_token_cross_entropy(perfect_logits, perfect_labels)

    shifted_x, shifted_y = causal_shift_labels(torch.tensor([[10, 11, 12, 13]], dtype=torch.long))

    padded = labels.clone()
    padded[:, -1] = -100
    padded_loss, padded_count = per_token_cross_entropy(uniform_logits, padded)

    return {
        "vocab_size": vocab_size,
        "uniform_logits_loss": float(uniform_loss.item()),
        "uniform_logits_expected_log_vocab": expected,
        "uniform_logits_abs_error": abs(float(uniform_loss.item()) - expected),
        "uniform_non_padding_tokens": uniform_count,
        "perfect_prediction_loss": float(perfect_loss.item()),
        "perfect_prediction_ppl": math.exp(float(perfect_loss.item())),
        "perfect_non_padding_tokens": perfect_count,
        "shift_input": shifted_x.tolist(),
        "shift_labels": shifted_y.tolist(),
        "padding_loss": float(padded_loss.item()),
        "padding_non_padding_tokens": padded_count,
        "passed": (
            abs(float(uniform_loss.item()) - expected) < 1e-4
            and float(perfect_loss.item()) < 1e-4
            and shifted_x.tolist() == [[10, 11, 12]]
            and shifted_y.tolist() == [[11, 12, 13]]
            and padded_count == 5
        ),
    }


def run_lm_evaluation(config: EvaluationConfig, output_dir: Path, root: Path) -> EvaluationResult:
    training_manifest = read_json(config.training_manifest_path, root)
    metrics = read_json(str(training_manifest["metrics_path"]), root)
    if training_manifest.get("scope") == "smoke" and config.scope != "smoke":
        raise ValueError("Step 5 smoke training manifest can only be evaluated with scope=smoke")
    tokens_seen = float(metrics.get("tokens_seen", 0) or 0)
    validation_loss = float(metrics.get("validation_loss", 0.0) or 0.0)
    lm_metrics = {
        "train_loss_final": metrics.get("train_loss_final"),
        "validation_loss": metrics.get("validation_loss"),
        "validation_ppl": metrics.get("validation_ppl"),
        "tokens_seen": metrics.get("tokens_seen"),
        "loss_per_token_diagnostic": validation_loss / max(1.0, tokens_seen),
        "budget_normalized_ppl_diagnostic": float(metrics.get("validation_ppl", 0.0) or 0.0) / max(1.0, tokens_seen),
        "token_normalized_loss_policy": "smoke_diagnostic_only",
        "main_evidence": False,
        "effectiveness_claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "lm_metrics.json"
    report_path = output_dir / "lm_evaluation_report.md"
    write_json(metrics_path, lm_metrics)
    write_text(
        report_path,
        simple_report(
            "LM Smoke Evaluation",
            lm_metrics,
            "Step 5 validation metrics are smoke diagnostics only and are not main PPL evidence.",
        ),
    )
    manifest = create_evaluation_manifest(
        config=config,
        root=root,
        metrics_path=metrics_path,
        report_path=report_path,
        completed=True,
        notes="LM smoke evaluation wrapper; no main table update.",
    )
    manifest_path = output_dir / "evaluation_manifest.json"
    write_manifest(manifest_path, manifest)
    return EvaluationResult(
        evaluation_name=config.evaluation_name,
        evaluation_type=config.evaluation_type,
        method_name=config.method_name,
        dataset_name=config.dataset_name,
        scope=config.scope,
        metrics=lm_metrics,
        summary={"source_training_manifest": config.training_manifest_path, "smoke_only": config.smoke_only},
        input_hashes={config.training_manifest_path: sha256_file(resolve_path(config.training_manifest_path, root))},
        output_paths={"metrics": metrics_path.as_posix(), "report": report_path.as_posix(), "manifest": manifest_path.as_posix()},
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        completed=True,
        notes="Smoke diagnostic only.",
    )
