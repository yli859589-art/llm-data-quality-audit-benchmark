from __future__ import annotations

import torch

from dataaudit_lm.evaluation.lm_metrics import NLLResult, token_weighted_nll_from_logits
from dataaudit_lm.evaluation.masking import target_span_mask


def score_target_only(
    logits: torch.Tensor,
    labels: torch.Tensor,
    *,
    prompt_lengths: list[int],
    ignore_index: int = -100,
) -> NLLResult:
    mask = target_span_mask(labels, prompt_lengths=prompt_lengths)
    return token_weighted_nll_from_logits(
        logits,
        labels,
        target_mask=mask,
        ignore_index=ignore_index,
    )
