from __future__ import annotations

import math

import torch
from torch import nn

from evaluation_v2.lm_metrics import ppl_from_nll


@torch.no_grad()
def evaluate_loss(
    model: nn.Module,
    blocks_x: torch.Tensor,
    blocks_y: torch.Tensor,
    *,
    device: str,
    max_batches: int = 4,
) -> tuple[float, float]:
    model.eval()
    losses: list[float] = []
    count = min(len(blocks_x), max_batches)
    for index in range(count):
        x = blocks_x[index : index + 1].to(device)
        y = blocks_y[index : index + 1].to(device)
        _, loss = model(x, y)
        if loss is not None:
            losses.append(float(loss.detach().cpu()))
    model.train()
    loss_value = sum(losses) / max(1, len(losses))
    return loss_value, math.exp(min(20.0, loss_value))


@torch.no_grad()
def evaluate_lm_nll(
    model: nn.Module,
    blocks_x: torch.Tensor,
    blocks_y: torch.Tensor,
    *,
    device: str,
    max_batches: int | None = None,
) -> dict[str, object]:
    """Evaluate causal LM mean token NLL without PPL clipping."""
    was_training = model.training
    model.eval()
    losses: list[float] = []
    batch_count = len(blocks_x) if max_batches is None else min(len(blocks_x), max_batches)
    for index in range(batch_count):
        x = blocks_x[index : index + 1].to(device)
        y = blocks_y[index : index + 1].to(device)
        _, loss = model(x, y)
        if loss is not None:
            losses.append(float(loss.detach().cpu()))
    if was_training:
        model.train()
    nll = sum(losses) / max(1, len(losses))
    payload = ppl_from_nll(nll)
    payload.update({"evaluated_batches": len(losses), "dropout_disabled": True})
    return payload
