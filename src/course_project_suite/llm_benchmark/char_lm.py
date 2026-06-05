from __future__ import annotations

import hashlib
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from course_project_suite.cs224n.gpt2 import GPT2Config, MiniGPT2


@dataclass(frozen=True)
class TrainConfig:
    block_size: int = 32
    batch_size: int = 8
    steps: int = 120
    eval_interval: int = 20
    eval_batches: int = 4
    learning_rate: float = 3e-3
    n_layer: int = 1
    n_head: int = 2
    n_embd: int = 32
    seed: int = 23
    device: str = "cpu"
    gradient_clip_norm: float = 1.0
    checkpoint_path: str | None = None


class CharVocab:
    def __init__(self, text: str):
        chars = sorted(set(text))
        if not chars:
            raise ValueError("Cannot build a vocabulary from empty text.")
        self.stoi = {char: index for index, char in enumerate(chars)}
        self.itos = {index: char for char, index in self.stoi.items()}

    def encode(self, text: str) -> list[int]:
        return [self.stoi[char] for char in text if char in self.stoi]

    def decode(self, ids: list[int]) -> str:
        return "".join(self.itos[index] for index in ids)

    def __len__(self) -> int:
        return len(self.stoi)

    @property
    def fingerprint(self) -> str:
        ordered = "".join(self.itos[index] for index in range(len(self.itos)))
        return hashlib.sha256(ordered.encode("utf-8")).hexdigest()


def _batch(
    data: torch.Tensor, config: TrainConfig, generator: torch.Generator
) -> tuple[torch.Tensor, torch.Tensor]:
    high = len(data) - config.block_size - 1
    if high <= 0:
        raise ValueError("Text is too short for the configured block size.")
    starts = torch.randint(high, (config.batch_size,), generator=generator)
    x = torch.stack([data[start : start + config.block_size] for start in starts])
    y = torch.stack([data[start + 1 : start + config.block_size + 1] for start in starts])
    return x.to(config.device), y.to(config.device)


@torch.no_grad()
def _evaluate(
    model: MiniGPT2,
    data: torch.Tensor,
    config: TrainConfig,
    generator: torch.Generator,
) -> tuple[float, float, int]:
    model.eval()
    losses = []
    correct = 0
    total = 0
    for _ in range(config.eval_batches):
        x, y = _batch(data, config, generator)
        logits, loss = model(x, y)
        losses.append(float(loss.detach()))
        correct += int((logits.argmax(dim=-1) == y).sum())
        total += y.numel()
    model.train()
    return sum(losses) / len(losses), correct / max(1, total), total


def train_character_lm(
    train_text: str, val_text: str, shared_vocab_text: str, config: TrainConfig
) -> dict[str, object]:
    torch.manual_seed(config.seed)
    vocab = CharVocab(shared_vocab_text)
    train_ids = torch.tensor(vocab.encode(train_text), dtype=torch.long)
    val_ids = torch.tensor(vocab.encode(val_text), dtype=torch.long)
    model_config = GPT2Config(
        vocab_size=len(vocab),
        block_size=config.block_size,
        n_layer=config.n_layer,
        n_head=config.n_head,
        n_embd=config.n_embd,
    )
    model = MiniGPT2(model_config).to(config.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate)
    train_generator = torch.Generator().manual_seed(config.seed)
    eval_generator = torch.Generator().manual_seed(config.seed + 1)
    curve = []
    if config.device.startswith("cuda") and torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    started = time.perf_counter()
    for step in range(config.steps + 1):
        if step % config.eval_interval == 0 or step == config.steps:
            train_loss, train_accuracy, train_eval_tokens = _evaluate(
                model,
                train_ids,
                config,
                eval_generator,
            )
            val_loss, val_accuracy, val_eval_tokens = _evaluate(
                model,
                val_ids,
                config,
                eval_generator,
            )
            curve.append(
                {
                    "step": step,
                    "train_loss": train_loss,
                    "train_next_char_accuracy": train_accuracy,
                    "train_evaluated_tokens": train_eval_tokens,
                    "val_loss": val_loss,
                    "val_next_char_accuracy": val_accuracy,
                    "val_evaluated_tokens": val_eval_tokens,
                }
            )
        if step == config.steps:
            break
        x, y = _batch(train_ids, config, train_generator)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.gradient_clip_norm)
        optimizer.step()
    elapsed = time.perf_counter() - started
    if config.checkpoint_path:
        checkpoint = Path(config.checkpoint_path)
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"model": model.state_dict(), "config": asdict(config)}, checkpoint)
    final_val_loss = curve[-1]["val_loss"]
    model.eval()
    with torch.no_grad():
        prompt_ids = val_ids[: config.block_size].tolist()
        generated = list(prompt_ids)
        context = torch.tensor(
            [generated[-config.block_size :]], dtype=torch.long, device=config.device
        )
        for _ in range(80):
            logits, _ = model(context)
            next_id = int(torch.argmax(logits[0, -1]).detach().cpu())
            generated.append(next_id)
            context = torch.tensor(
                [generated[-config.block_size :]], dtype=torch.long, device=config.device
            )
    sample_prompt = vocab.decode(prompt_ids)
    sample_generation = vocab.decode(generated)
    return {
        "config": asdict(config),
        "tokenizer": "character",
        "tokenizer_type": "character_shared",
        "tokenizer_id": "shared_character_vocab_from_wikitext2_train",
        "tokenizer_hash": vocab.fingerprint,
        "model": "decoder-only causal MiniGPT",
        "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
        "vocab_size": len(vocab),
        "train_characters": len(train_ids),
        "validation_characters": len(val_ids),
        "evaluated_validation_tokens": curve[-1]["val_evaluated_tokens"],
        "eval_batches": config.eval_batches,
        "eval_batch_size": config.batch_size,
        "eval_block_size": config.block_size,
        "eval_token_budget": config.eval_batches * config.batch_size * config.block_size,
        "eval_coverage_ratio": curve[-1]["val_evaluated_tokens"] / max(1, len(val_ids)),
        "elapsed_seconds": elapsed,
        "tokens_per_second": config.steps
        * config.batch_size
        * config.block_size
        / max(elapsed, 1e-12),
        "peak_cuda_memory_bytes": (
            torch.cuda.max_memory_allocated()
            if config.device.startswith("cuda") and torch.cuda.is_available()
            else None
        ),
        "final_train_loss": curve[-1]["train_loss"],
        "final_val_loss": final_val_loss,
        "final_val_perplexity": math.exp(final_val_loss),
        "final_val_bits_per_character": final_val_loss / math.log(2),
        "final_val_next_char_accuracy": curve[-1]["val_next_char_accuracy"],
        "sample_prompt": sample_prompt,
        "sample_generation": sample_generation,
        "curve": curve,
    }
