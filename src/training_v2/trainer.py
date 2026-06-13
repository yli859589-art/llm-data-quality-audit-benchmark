from __future__ import annotations

import math
import random
import time
from pathlib import Path
from typing import Any

import torch

from models_v2.config import ModelConfig
from models_v2.decoder_lm import DecoderLM

from .checkpoint import save_checkpoint
from .config import TrainingConfig
from .data_adapter import build_tokenized_training_data
from .evaluator import evaluate_loss
from .manifest import create_training_manifest, write_json
from .registry import append_training_registry
from .validation import validate_training_manifest


def _device(requested: str) -> str:
    if requested.startswith("cuda") and not torch.cuda.is_available():
        return "cpu"
    return requested


def _sample_batch(
    blocks_x: torch.Tensor,
    blocks_y: torch.Tensor,
    batch_size: int,
    generator: torch.Generator,
    device: str,
) -> tuple[torch.Tensor, torch.Tensor]:
    indices = torch.randint(len(blocks_x), (batch_size,), generator=generator)
    return blocks_x[indices].to(device), blocks_y[indices].to(device)


def run_training(
    *,
    training_config: TrainingConfig,
    model_config: ModelConfig,
    root: Path,
) -> dict[str, Any]:
    random.seed(training_config.seed)
    torch.manual_seed(training_config.seed)
    device = _device(training_config.device)
    output_dir = root / training_config.output_dir if not Path(training_config.output_dir).is_absolute() else Path(training_config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data = build_tokenized_training_data(
        dataset_path=training_config.dataset_path,
        dataset_manifest_path=training_config.dataset_manifest_path,
        tokenizer_manifest_path=training_config.tokenizer_manifest_path,
        context_length=model_config.context_length,
        root=root,
    )
    if max(data.token_ids) >= model_config.vocab_size:
        raise ValueError("model vocab_size is smaller than encoded tokenizer ids")
    model = DecoderLM(model_config).to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=training_config.learning_rate,
        weight_decay=training_config.weight_decay,
    )
    generator = torch.Generator().manual_seed(training_config.seed)
    curve: list[dict[str, float | int]] = []
    started = time.perf_counter()
    final_train_loss = 0.0
    for step in range(1, training_config.max_steps + 1):
        model.train()
        x, y = _sample_batch(
            data.blocks_x,
            data.blocks_y,
            training_config.batch_size,
            generator,
            device,
        )
        _, loss = model(x, y)
        assert loss is not None
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        if training_config.gradient_clip:
            torch.nn.utils.clip_grad_norm_(model.parameters(), training_config.gradient_clip)
        optimizer.step()
        final_train_loss = float(loss.detach().cpu())
        if step % training_config.eval_interval == 0 or step == training_config.max_steps:
            val_loss, val_ppl = evaluate_loss(
                model,
                data.blocks_x,
                data.blocks_y,
                device=device,
                max_batches=4,
            )
            curve.append(
                {
                    "step": step,
                    "train_loss": final_train_loss,
                    "validation_loss": val_loss,
                    "validation_ppl": val_ppl,
                }
            )
    if not curve:
        val_loss, val_ppl = evaluate_loss(model, data.blocks_x, data.blocks_y, device=device, max_batches=4)
        curve.append({"step": 0, "train_loss": final_train_loss, "validation_loss": val_loss, "validation_ppl": val_ppl})
    elapsed = time.perf_counter() - started
    tokens_seen = training_config.max_steps * training_config.batch_size * model_config.context_length
    metrics = {
        "status": "completed",
        "scope": training_config.scope,
        "smoke_only": training_config.smoke_only,
        "experiment_name": training_config.experiment_name,
        "model_name": model_config.model_name,
        "scale_class": model_config.scale_class,
        "tokenizer_type": data.summary["tokenizer_type"],
        "tokenizer_hash": data.summary["tokenizer_hash"],
        "seed": training_config.seed,
        "max_steps": training_config.max_steps,
        "batch_size": training_config.batch_size,
        "context_length": model_config.context_length,
        "tokens_seen": tokens_seen,
        "train_loss_final": final_train_loss,
        "validation_loss": curve[-1]["validation_loss"],
        "validation_ppl": math.exp(min(20.0, float(curve[-1]["validation_loss"]))),
        "elapsed_seconds": elapsed,
        "tokens_per_second": tokens_seen / max(elapsed, 1e-12),
        "loss_curve": curve,
        "data_summary": data.summary,
        "notes": "Step 5 smoke metrics are not main evidence and must not enter main_results.",
    }
    metrics_path = output_dir / "metrics.json"
    write_json(metrics_path, metrics)
    checkpoint_info = save_checkpoint(
        model=model,
        output_dir=output_dir,
        root=root,
        payload={
            "model_config": model_config.to_dict(),
            "training_config": training_config.to_dict(),
            "scope": training_config.scope,
            "smoke_only": training_config.smoke_only,
        },
        enabled=training_config.save_checkpoint,
    )
    manifest = create_training_manifest(
        config=training_config,
        model_config=model_config,
        root=root,
        metrics_path=metrics_path,
        metrics=metrics,
        checkpoint_info=checkpoint_info,
        data_summary=data.summary,
        completed=True,
        implemented_but_not_run=False,
    )
    manifest_path = output_dir / "training_manifest.json"
    write_json(manifest_path, manifest)
    validate_training_manifest(manifest, root)
    append_training_registry(root, manifest)
    return {
        "manifest": manifest,
        "manifest_path": manifest_path,
        "metrics": metrics,
        "checkpoint_info": checkpoint_info,
    }
