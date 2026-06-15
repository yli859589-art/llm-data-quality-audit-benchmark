from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch.nn import functional as F

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.evaluation.lm_metrics import token_weighted_nll_from_logits
from dataaudit_lm.integrity.io import write_json
from dataaudit_lm.models.config import DecoderLMConfig
from dataaudit_lm.training.batching import make_causal_blocks
from dataaudit_lm.training.checkpoints import save_checkpoint
from dataaudit_lm.training.initialization import create_initialized_model


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


@dataclass(frozen=True)
class TrainingConfig:
    seed: int = 13
    steps: int = 5
    learning_rate: float = 1e-3
    token_budget: int = 512
    batch_size: int = 4
    warm_start: bool = False


def run_tiny_training(
    *,
    records: list[DataRecord],
    model_config: DecoderLMConfig,
    training_config: TrainingConfig,
    output_dir: Path,
) -> dict[str, object]:
    if training_config.warm_start:
        raise ValueError("DataAudit-LM formal/rehearsal training requires warm_start=false")
    output_dir.mkdir(parents=True, exist_ok=True)
    model, fingerprint = create_initialized_model(training_config.seed, model_config)
    optimizer = torch.optim.AdamW(model.parameters(), lr=training_config.learning_rate)
    blocks = make_causal_blocks(
        [record.text for record in records],
        context_length=model_config.context_length,
        vocab_size=model_config.vocab_size,
    )
    tokens_seen = 0
    last_loss = 0.0
    for step in range(training_config.steps):
        batch = blocks[step % len(blocks) : step % len(blocks) + 1]
        if batch.numel() == 0:
            batch = blocks[:1]
        inputs = batch[:, :-1]
        labels = batch[:, 1:]
        logits = model(inputs)
        loss = F.cross_entropy(logits.reshape(-1, model_config.vocab_size), labels.reshape(-1))
        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        tokens_seen += int(labels.numel())
        last_loss = float(loss.detach().cpu().item())
    with torch.no_grad():
        eval_batch = blocks[: min(len(blocks), training_config.batch_size)]
        logits = model(eval_batch[:, :-1])
        labels = eval_batch[:, 1:]
        valid_nll = token_weighted_nll_from_logits(logits, labels).nll
    checkpoint = save_checkpoint(
        output_dir / "final_checkpoint.pt",
        {"config": model_config.to_dict(), "state_dict": model.state_dict()},
    )
    metrics = {
        "steps_completed": training_config.steps,
        "tokens_seen": tokens_seen,
        "train_loss_final": last_loss,
        "valid_nll_nats_per_token": valid_nll,
        "warm_start": False,
        "initialization_fingerprint": fingerprint,
        **checkpoint,
    }
    write_json(output_dir / "metrics.json", metrics)
    write_json(
        output_dir / "training_manifest.json",
        {
            "manifest_version": "dataaudit_lm_training_manifest_v1",
            "seed": training_config.seed,
            "warm_start": False,
            "initialization_fingerprint": fingerprint,
            "steps_completed": training_config.steps,
            "tokens_seen": tokens_seen,
            "metrics_path": _display_path(output_dir / "metrics.json"),
            **checkpoint,
        },
    )
    return metrics
