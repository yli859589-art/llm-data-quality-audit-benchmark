from __future__ import annotations

from .base import BaseTokenizer, TokenizerConfig
from .manifest import combined_tokenizer_hash


class OptionalDependencyUnavailable(RuntimeError):
    pass


class GPT2OptionalTokenizer(BaseTokenizer):
    tokenizer_type = "gpt2_optional"

    def __init__(self, config: TokenizerConfig | None = None) -> None:
        super().__init__(config)
        self.backend = None
        self.backend_name = ""
        try:
            import tiktoken  # type: ignore

            self.backend = tiktoken.get_encoding("gpt2")
            self.backend_name = "tiktoken"
        except Exception:
            try:
                from transformers import GPT2TokenizerFast  # type: ignore

                self.backend = GPT2TokenizerFast.from_pretrained("gpt2", local_files_only=True)
                self.backend_name = "transformers_local"
            except Exception as exc:
                self._unavailable_reason = f"{type(exc).__name__}: {exc}"

    @property
    def available(self) -> bool:
        return self.backend is not None

    @property
    def unavailable_reason(self) -> str:
        return getattr(self, "_unavailable_reason", "")

    def _require(self) -> None:
        if self.backend is None:
            raise OptionalDependencyUnavailable(self.unavailable_reason or "GPT-2 tokenizer backend unavailable")

    def train(self, texts: list[str]) -> "GPT2OptionalTokenizer":
        return self

    def encode(self, text: str) -> list[int]:
        self._require()
        return list(self.backend.encode(text))  # type: ignore[union-attr]

    def decode(self, ids: list[int]) -> str:
        self._require()
        return str(self.backend.decode(ids))  # type: ignore[union-attr]

    def save(self, path) -> None:
        self._require()
        raise NotImplementedError("GPT-2 optional wrapper does not save external tokenizer assets")

    @classmethod
    def load(cls, path) -> "GPT2OptionalTokenizer":
        return cls()

    @property
    def vocab_size(self) -> int:
        if self.backend is None:
            return 0
        value = getattr(self.backend, "n_vocab", None)
        if value is not None:
            return int(value)
        return int(getattr(self.backend, "vocab_size", 0))

    @property
    def tokenizer_hash(self) -> str:
        return combined_tokenizer_hash(
            tokenizer_type=self.tokenizer_type,
            tokenizer_name=self.config.tokenizer_name if self.config else "gpt2_optional",
            extra={"backend": self.backend_name, "available": self.available},
        )
