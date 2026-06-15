from __future__ import annotations

import torch


def target_span_mask(labels: torch.Tensor, *, prompt_lengths: list[int]) -> torch.Tensor:
    if labels.ndim != 2:
        raise ValueError("labels must have shape [batch, sequence]")
    if len(prompt_lengths) != labels.size(0):
        raise ValueError("prompt_lengths length must match batch size")
    mask = torch.zeros_like(labels, dtype=torch.bool)
    for row, prompt_length in enumerate(prompt_lengths):
        if prompt_length >= labels.size(1):
            raise ValueError("each example must contain at least one target token")
        mask[row, prompt_length:] = True
    return mask
