from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TokenizerConfig:
    tokenizer_name: str
    tokenizer_type: str
    vocab_size: int
    training_data_path: str
    training_scope: str
    seed: int
    normalization: str
    model_path: str
    vocab_path: str
    manifest_path: str
    optional_dependency: str = ""
    fallback_allowed: bool = False
    smoke_only: bool = False
    notes: str = ""
    scope: str = "smoke"
    level3_mainline: bool = False


@dataclass(frozen=True)
class TokenizerManifest:
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)


class BaseTokenizer:
    tokenizer_type = "base"

    def __init__(self, config: TokenizerConfig | None = None) -> None:
        self.config = config

    def train(self, texts: list[str]) -> "BaseTokenizer":
        raise NotImplementedError

    def encode(self, text: str) -> list[int]:
        raise NotImplementedError

    def decode(self, ids: list[int]) -> str:
        raise NotImplementedError

    def save(self, path: str | Path) -> None:
        raise NotImplementedError

    @classmethod
    def load(cls, path: str | Path) -> "BaseTokenizer":
        raise NotImplementedError

    @property
    def vocab_size(self) -> int:
        raise NotImplementedError

    @property
    def tokenizer_id(self) -> str:
        name = self.config.tokenizer_name if self.config else self.__class__.__name__
        return f"{self.tokenizer_type}:{name}"

    @property
    def tokenizer_hash(self) -> str:
        raise NotImplementedError

    def count_tokens(self, text: str) -> int:
        return len(self.encode(text))

    def write_manifest(self, path: str | Path, **kwargs: Any) -> dict[str, Any]:
        from .manifest import create_tokenizer_manifest, write_tokenizer_manifest

        manifest = create_tokenizer_manifest(tokenizer=self, **kwargs)
        write_tokenizer_manifest(Path(path), manifest)
        return manifest
