from __future__ import annotations

import json
from pathlib import Path

from course_project_suite.llm_benchmark.char_lm import CharVocab

from .base import BaseTokenizer, TokenizerConfig
from .manifest import combined_tokenizer_hash


class CharTokenizer(BaseTokenizer):
    tokenizer_type = "char"

    def __init__(self, config: TokenizerConfig | None = None, chars: list[str] | None = None) -> None:
        super().__init__(config)
        self._chars = sorted(chars or [])
        self._vocab = CharVocab("".join(self._chars)) if self._chars else None

    def train(self, texts: list[str]) -> "CharTokenizer":
        text = "".join(texts)
        self._vocab = CharVocab(text)
        self._chars = [self._vocab.itos[index] for index in range(len(self._vocab))]
        return self

    def encode(self, text: str) -> list[int]:
        if self._vocab is None:
            raise ValueError("CharTokenizer is not trained or loaded")
        return self._vocab.encode(text)

    def decode(self, ids: list[int]) -> str:
        if self._vocab is None:
            raise ValueError("CharTokenizer is not trained or loaded")
        return self._vocab.decode(ids)

    def save(self, path: str | Path) -> None:
        if self._vocab is None:
            raise ValueError("CharTokenizer is not trained")
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"chars": self._chars}, indent=2, sort_keys=True), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "CharTokenizer":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(chars=list(payload["chars"]))

    @property
    def vocab_size(self) -> int:
        return len(self._chars)

    @property
    def tokenizer_hash(self) -> str:
        return combined_tokenizer_hash(
            tokenizer_type=self.tokenizer_type,
            tokenizer_name=self.config.tokenizer_name if self.config else "char",
            extra={"chars": self._chars},
        )
