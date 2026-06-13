from __future__ import annotations

from pathlib import Path

import pytest

from tokenization.base import TokenizerConfig
from tokenization.bpe_tokenizer import LightweightBPETokenizer
from tokenization.char_tokenizer import CharTokenizer
from tokenization.gpt2_tokenizer import GPT2OptionalTokenizer, OptionalDependencyUnavailable


def _config(tmp_path: Path, tokenizer_name: str, tokenizer_type: str) -> TokenizerConfig:
    return TokenizerConfig(
        tokenizer_name=tokenizer_name,
        tokenizer_type=tokenizer_type,
        vocab_size=64,
        training_data_path="unit.jsonl",
        training_scope="smoke",
        seed=42,
        normalization="identity",
        model_path=(tmp_path / "model.json").as_posix(),
        vocab_path=(tmp_path / "vocab.json").as_posix(),
        manifest_path=(tmp_path / "tokenizer_manifest.json").as_posix(),
        smoke_only=True,
    )


def test_char_tokenizer_wraps_existing_char_vocab(tmp_path: Path) -> None:
    tokenizer = CharTokenizer(_config(tmp_path, "char_unit", "char")).train(["hello world"])

    encoded = tokenizer.encode("hello")

    assert encoded
    assert tokenizer.decode(encoded) == "hello"
    assert tokenizer.count_tokens("hello") == len(encoded)
    assert tokenizer.vocab_size >= len(set("hello world"))


def test_lightweight_bpe_tokenizer_trains_saves_and_loads(tmp_path: Path) -> None:
    config = _config(tmp_path, "bpe_unit", "lightweight_bpe_smoke")
    tokenizer = LightweightBPETokenizer(config).train(["alpha beta alpha", "beta gamma"])
    model_path = tmp_path / "tokenizer.json"

    tokenizer.save(model_path)
    loaded = LightweightBPETokenizer.load(model_path)

    assert loaded.vocab_size > 0
    assert loaded.encode("alpha beta")
    assert isinstance(loaded.decode(loaded.encode("alpha")), str)


def test_gpt2_optional_wrapper_is_offline_safe() -> None:
    tokenizer = GPT2OptionalTokenizer()

    if tokenizer.available:
        assert tokenizer.encode("hello")
        assert isinstance(tokenizer.decode(tokenizer.encode("hello")), str)
        assert tokenizer.vocab_size > 0
    else:
        assert tokenizer.vocab_size == 0
        with pytest.raises(OptionalDependencyUnavailable):
            tokenizer.encode("hello")
