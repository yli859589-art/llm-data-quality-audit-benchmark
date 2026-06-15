from __future__ import annotations

import torch


def encode_bytes(text: str, *, vocab_size: int = 128) -> list[int]:
    return [byte % vocab_size for byte in text.encode("utf-8")]


def make_causal_blocks(texts: list[str], *, context_length: int, vocab_size: int) -> torch.Tensor:
    tokens = [token for text in texts for token in encode_bytes(text, vocab_size=vocab_size)]
    if len(tokens) < context_length + 1:
        tokens = tokens + [0] * (context_length + 1 - len(tokens))
    blocks = []
    for start in range(0, max(1, len(tokens) - context_length), context_length):
        block = tokens[start : start + context_length + 1]
        if len(block) == context_length + 1:
            blocks.append(block)
    return torch.tensor(blocks or [tokens[: context_length + 1]], dtype=torch.long)
