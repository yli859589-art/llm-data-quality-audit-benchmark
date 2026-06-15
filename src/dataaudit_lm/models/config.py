from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DecoderLMConfig:
    vocab_size: int = 128
    context_length: int = 32
    embedding_dim: int = 32
    hidden_dim: int = 48
    num_layers: int = 1
    dropout: float = 0.0

    def to_dict(self) -> dict[str, int | float]:
        return asdict(self)
