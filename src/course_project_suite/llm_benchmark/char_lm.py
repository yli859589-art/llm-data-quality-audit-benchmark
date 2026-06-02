from __future__ import annotations
from dataclasses import asdict, dataclass
import math
import time

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
    device: str = 'cpu'


class CharVocab:
    def __init__(self, text: str):
        chars = sorted(set(text))
        if not chars:
            raise ValueError('Cannot build a vocabulary from empty text.')
        self.stoi = {char: index for index, char in enumerate(chars)}
        self.itos = {index: char for char, index in self.stoi.items()}

    def encode(self, text: str) -> list[int]:
        return [self.stoi[char] for char in text if char in self.stoi]

    def decode(self, ids: list[int]) -> str:
        return ''.join(self.itos[index] for index in ids)

    def __len__(self) -> int:
        return len(self.stoi)


def _batch(data: torch.Tensor, config: TrainConfig, generator: torch.Generator) -> tuple[torch.Tensor, torch.Tensor]:
    high = len(data) - config.block_size - 1
    if high <= 0:
        raise ValueError('Text is too short for the configured block size.')
    starts = torch.randint(high, (config.batch_size,), generator=generator)
    x = torch.stack([data[start:start + config.block_size] for start in starts])
    y = torch.stack([data[start + 1:start + config.block_size + 1] for start in starts])
    return x.to(config.device), y.to(config.device)


@torch.no_grad()
def _evaluate(model: MiniGPT2, data: torch.Tensor, config: TrainConfig, generator: torch.Generator) -> float:
    model.eval()
    losses = []
    for _ in range(config.eval_batches):
        x, y = _batch(data, config, generator)
        _, loss = model(x, y)
        losses.append(float(loss.detach()))
    model.train()
    return sum(losses) / len(losses)


def train_character_lm(train_text: str, val_text: str, shared_vocab_text: str, config: TrainConfig) -> dict[str, object]:
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
    started = time.perf_counter()
    for step in range(config.steps + 1):
        if step % config.eval_interval == 0 or step == config.steps:
            curve.append({
                'step': step,
                'train_loss': _evaluate(model, train_ids, config, eval_generator),
                'val_loss': _evaluate(model, val_ids, config, eval_generator),
            })
        if step == config.steps:
            break
        x, y = _batch(train_ids, config, train_generator)
        _, loss = model(x, y)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
    elapsed = time.perf_counter() - started
    final_val_loss = curve[-1]['val_loss']
    return {
        'config': asdict(config),
        'vocab_size': len(vocab),
        'train_characters': len(train_ids),
        'validation_characters': len(val_ids),
        'elapsed_seconds': elapsed,
        'tokens_per_second': config.steps * config.batch_size * config.block_size / max(elapsed, 1e-12),
        'final_train_loss': curve[-1]['train_loss'],
        'final_val_loss': final_val_loss,
        'final_val_perplexity': math.exp(final_val_loss),
        'curve': curve,
    }
