from __future__ import annotations

import torch
from torch import nn

from dataaudit_lm.models.config import DecoderLMConfig


class TinyDecoderLM(nn.Module):
    def __init__(self, config: DecoderLMConfig) -> None:
        super().__init__()
        self.config = config
        self.embedding = nn.Embedding(config.vocab_size, config.embedding_dim)
        self.rnn = nn.GRU(
            input_size=config.embedding_dim,
            hidden_size=config.hidden_dim,
            num_layers=config.num_layers,
            batch_first=True,
            dropout=config.dropout if config.num_layers > 1 else 0.0,
        )
        self.output = nn.Linear(config.hidden_dim, config.vocab_size)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        embedded = self.embedding(input_ids)
        hidden, _ = self.rnn(embedded)
        return self.output(hidden)
