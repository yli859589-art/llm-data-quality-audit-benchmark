from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch.nn import functional as F


@dataclass(frozen=True)
class NLLResult:
    nll: float
    total_nll: float
    valid_tokens: int
    ppl: float | None
    ppl_overflow: bool


def causal_shift(input_ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    if input_ids.ndim != 2 or input_ids.size(1) < 2:
        raise ValueError("input_ids must have shape [batch, sequence>=2]")
    return input_ids[:, :-1].contiguous(), input_ids[:, 1:].contiguous()


def token_weighted_nll_from_logits(
    logits: torch.Tensor,
    labels: torch.Tensor,
    *,
    target_mask: torch.Tensor | None = None,
    ignore_index: int = -100,
) -> NLLResult:
    if logits.ndim != 3:
        raise ValueError("logits must have shape [batch, sequence, vocab]")
    if labels.shape != logits.shape[:2]:
        raise ValueError("labels must match logits batch and sequence dimensions")
    valid = labels.ne(ignore_index)
    if target_mask is not None:
        if target_mask.shape != labels.shape:
            raise ValueError("target_mask must match labels")
        valid = valid & target_mask.bool()
    if not bool(valid.any()):
        raise ValueError("at least one valid target token is required")
    safe_labels = labels.masked_fill(~valid, ignore_index)
    vocab_size = logits.size(-1)
    loss_sum = F.cross_entropy(
        logits.reshape(-1, vocab_size),
        safe_labels.reshape(-1),
        ignore_index=ignore_index,
        reduction="sum",
    )
    valid_tokens = int(valid.sum().item())
    total_nll = float(loss_sum.detach().cpu().item())
    nll = total_nll / valid_tokens
    overflow = nll > math.log(float("1.7976931348623157e308"))
    return NLLResult(
        nll=nll,
        total_nll=total_nll,
        valid_tokens=valid_tokens,
        ppl=None if overflow else math.exp(nll),
        ppl_overflow=overflow,
    )


def ppl_from_nll(nll: float) -> dict[str, float | bool | None]:
    overflow = nll > math.log(float("1.7976931348623157e308"))
    return {
        "valid_nll_nats_per_token": nll,
        "valid_ppl": None if overflow else math.exp(nll),
        "ppl_overflow": overflow,
        "ppl_clipped": False,
        "ppl_comparable": not overflow,
    }
