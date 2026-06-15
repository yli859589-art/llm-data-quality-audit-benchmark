from __future__ import annotations

import torch

from dataaudit_lm.evaluation.downstream import score_target_only


def test_downstream_target_only_scoring_ignores_prompt_tokens() -> None:
    labels = torch.tensor([[0, 1, 2, 3]])
    good_prompt_bad_target = torch.zeros((1, 4, 5))
    bad_prompt_bad_target = good_prompt_bad_target.clone()
    good_prompt_bad_target[0, 0, 0] = 50.0
    good_prompt_bad_target[0, 1, 1] = 50.0
    bad_prompt_bad_target[0, 0, 4] = 50.0
    bad_prompt_bad_target[0, 1, 4] = 50.0

    first = score_target_only(good_prompt_bad_target, labels, prompt_lengths=[2])
    second = score_target_only(bad_prompt_bad_target, labels, prompt_lengths=[2])

    assert first.valid_tokens == 2
    assert first.nll == second.nll
