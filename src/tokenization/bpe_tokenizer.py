from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .base import BaseTokenizer, TokenizerConfig
from .manifest import combined_tokenizer_hash


def _word_tokens(word: str) -> tuple[str, ...]:
    return tuple(list(word) + ["</w>"])


class LightweightBPETokenizer(BaseTokenizer):
    tokenizer_type = "lightweight_bpe_smoke"

    def __init__(
        self,
        config: TokenizerConfig | None = None,
        merges: list[tuple[str, str]] | None = None,
        vocab: dict[str, int] | None = None,
    ) -> None:
        super().__init__(config)
        self.merges = merges or []
        self.vocab = vocab or {}

    def train(self, texts: list[str]) -> "LightweightBPETokenizer":
        requested = self.config.vocab_size if self.config else 512
        words: Counter[tuple[str, ...]] = Counter()
        for text in texts:
            for word in text.strip().split():
                words[_word_tokens(word)] += 1
        target_merges = max(0, requested - 256)
        for _ in range(target_merges):
            pairs: Counter[tuple[str, str]] = Counter()
            for word, count in words.items():
                for left, right in zip(word, word[1:]):
                    pairs[(left, right)] += count
            if not pairs:
                break
            best = min((-count, pair) for pair, count in pairs.items())[1]
            self.merges.append(best)
            merged: Counter[tuple[str, ...]] = Counter()
            for word, count in words.items():
                out: list[str] = []
                index = 0
                while index < len(word):
                    if index < len(word) - 1 and (word[index], word[index + 1]) == best:
                        out.append(word[index] + word[index + 1])
                        index += 2
                    else:
                        out.append(word[index])
                        index += 1
                merged[tuple(out)] += count
            words = merged
            tokens = {token for word in words for token in word} | {"<unk>"}
            if len(tokens) >= requested:
                break
        tokens = sorted({token for word in words for token in word} | {"<unk>"})
        if len(tokens) > requested:
            tokens = tokens[: requested - 1] + ["<unk>"]
        self.vocab = {token: index for index, token in enumerate(tokens)}
        return self

    def encode_word(self, word: str) -> list[int]:
        tokens = list(word) + ["</w>"]
        for left, right in self.merges:
            out: list[str] = []
            index = 0
            while index < len(tokens):
                if index < len(tokens) - 1 and tokens[index] == left and tokens[index + 1] == right:
                    out.append(left + right)
                    index += 2
                else:
                    out.append(tokens[index])
                    index += 1
            tokens = out
        unk = self.vocab.get("<unk>", 0)
        return [self.vocab.get(token, unk) for token in tokens]

    def encode(self, text: str) -> list[int]:
        ids: list[int] = []
        for word in text.split():
            ids.extend(self.encode_word(word))
        return ids

    def decode(self, ids: list[int]) -> str:
        inv = {index: token for token, index in self.vocab.items()}
        text = "".join(inv.get(index, "<unk>") for index in ids)
        return text.replace("</w>", " ").strip()

    def save(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "tokenizer_type": self.tokenizer_type,
            "merges": self.merges,
            "vocab": self.vocab,
        }
        output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "LightweightBPETokenizer":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        merges = [tuple(item) for item in payload.get("merges", [])]
        vocab = {str(token): int(index) for token, index in payload.get("vocab", {}).items()}
        return cls(merges=merges, vocab=vocab)

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    @property
    def tokenizer_hash(self) -> str:
        return combined_tokenizer_hash(
            tokenizer_type=self.tokenizer_type,
            tokenizer_name=self.config.tokenizer_name if self.config else "lightweight_bpe_smoke",
            extra={"merges": self.merges, "vocab": self.vocab},
        )
