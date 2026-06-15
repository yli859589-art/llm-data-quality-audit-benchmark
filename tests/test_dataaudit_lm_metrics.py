from __future__ import annotations

import math

import torch

from dataaudit_lm.evaluation.lm_metrics import (
    causal_shift,
    ppl_from_nll,
    token_weighted_nll_from_logits,
)


def test_token_weighted_nll_uniform_perfect_masks_and_ppl_identity() -> None:
    labels = torch.tensor([[0, 1, -100], [2, -100, -100]])
    logits = torch.zeros((2, 3, 5))
    result = token_weighted_nll_from_logits(logits, labels)
    assert math.isclose(result.nll, math.log(5), rel_tol=1e-6)
    assert result.valid_tokens == 3
    assert math.isclose(result.ppl or 0.0, math.exp(result.nll), rel_tol=1e-6)

    perfect_labels = torch.tensor([[1, 2]])
    perfect_logits = torch.full((1, 2, 4), -40.0)
    perfect_logits[0, 0, 1] = 40.0
    perfect_logits[0, 1, 2] = 40.0
    perfect = token_weighted_nll_from_logits(perfect_logits, perfect_labels)
    assert perfect.nll < 1e-4

    shifted_x, shifted_y = causal_shift(torch.tensor([[10, 11, 12]]))
    assert shifted_x.tolist() == [[10, 11]]
    assert shifted_y.tolist() == [[11, 12]]

    target_mask = torch.tensor([[False, True, False], [True, False, False]])
    masked = token_weighted_nll_from_logits(logits, labels, target_mask=target_mask)
    assert masked.valid_tokens == 2
    assert ppl_from_nll(999.0)["ppl_overflow"] is True
