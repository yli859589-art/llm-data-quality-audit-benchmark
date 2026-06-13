from __future__ import annotations

import json
from pathlib import Path

import pytest

from tokenization.base import TokenizerConfig
from tokenization.bpe_tokenizer import LightweightBPETokenizer
from tokenization.manifest import MANIFEST_VERSION, create_tokenizer_manifest
from tokenization.validation import TokenizerManifestError, validate_tokenizer_manifest


def _write_jsonl(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                json.dumps({"text": "alpha beta alpha"}),
                json.dumps({"text": "gamma delta"}),
            ]
        ),
        encoding="utf-8",
    )


def _train_bpe(tmp_path: Path) -> tuple[LightweightBPETokenizer, Path, Path, Path]:
    data_path = tmp_path / "train.jsonl"
    model_path = tmp_path / "tokenizer.json"
    vocab_path = tmp_path / "vocab.json"
    _write_jsonl(data_path)
    config = TokenizerConfig(
        tokenizer_name="bpe_manifest_unit",
        tokenizer_type="lightweight_bpe_smoke",
        vocab_size=64,
        training_data_path=data_path.as_posix(),
        training_scope="smoke",
        seed=42,
        normalization="identity",
        model_path=model_path.as_posix(),
        vocab_path=vocab_path.as_posix(),
        manifest_path=(tmp_path / "tokenizer_manifest.json").as_posix(),
        fallback_allowed=True,
        smoke_only=True,
    )
    tokenizer = LightweightBPETokenizer(config).train(["alpha beta alpha", "gamma delta"])
    tokenizer.save(model_path)
    vocab_path.write_text(json.dumps(tokenizer.vocab, sort_keys=True), encoding="utf-8")
    return tokenizer, data_path, model_path, vocab_path


def test_tokenizer_manifest_schema_and_smoke_boundary(tmp_path: Path) -> None:
    tokenizer, data_path, model_path, vocab_path = _train_bpe(tmp_path)
    manifest = create_tokenizer_manifest(
        tokenizer=tokenizer,
        root=Path.cwd(),
        tokenizer_name="bpe_manifest_unit",
        tokenizer_type="lightweight_bpe_smoke",
        scope="smoke",
        level3_mainline=False,
        vocab_size_requested=64,
        vocab_size_actual=tokenizer.vocab_size,
        training_data_path=data_path.as_posix(),
        training_scope="smoke",
        seed=42,
        normalization="identity",
        model_path=model_path.as_posix(),
        vocab_path=vocab_path.as_posix(),
        fallback_used=True,
        fallback_type="lightweight_bpe_smoke",
        smoke_only=True,
        notes="unit smoke manifest",
    )

    validate_tokenizer_manifest(manifest, Path.cwd())

    assert manifest["manifest_version"] == MANIFEST_VERSION
    assert manifest["scope"] == "smoke"
    assert manifest["smoke_only"] is True
    assert manifest["level3_mainline"] is False
    assert manifest["training_data_hash"]
    assert manifest["tokenizer_hash"]


def test_smoke_manifest_cannot_claim_mainline(tmp_path: Path) -> None:
    tokenizer, data_path, model_path, vocab_path = _train_bpe(tmp_path)
    manifest = create_tokenizer_manifest(
        tokenizer=tokenizer,
        root=Path.cwd(),
        tokenizer_name="bpe_manifest_unit",
        tokenizer_type="lightweight_bpe_smoke",
        scope="smoke",
        level3_mainline=False,
        vocab_size_requested=64,
        vocab_size_actual=tokenizer.vocab_size,
        training_data_path=data_path.as_posix(),
        training_scope="smoke",
        seed=42,
        normalization="identity",
        model_path=model_path.as_posix(),
        vocab_path=vocab_path.as_posix(),
        fallback_used=True,
        fallback_type="lightweight_bpe_smoke",
        smoke_only=True,
        notes="unit smoke manifest",
    )
    manifest["level3_mainline"] = True

    with pytest.raises(TokenizerManifestError):
        validate_tokenizer_manifest(manifest, Path.cwd())


def test_optional_gpt2_manifest_can_be_implemented_but_not_run(tmp_path: Path) -> None:
    data_path = tmp_path / "train.jsonl"
    _write_jsonl(data_path)
    manifest = create_tokenizer_manifest(
        tokenizer=None,
        root=Path.cwd(),
        tokenizer_name="gpt2_optional_unit",
        tokenizer_type="gpt2_optional",
        scope="implemented_but_not_run",
        level3_mainline=False,
        vocab_size_requested=50257,
        vocab_size_actual=0,
        training_data_path=data_path.as_posix(),
        training_scope="implemented_but_not_run",
        seed=42,
        normalization="gpt2_native",
        model_path="",
        vocab_path="",
        optional_dependency="tiktoken_or_transformers",
        optional_dependency_available=False,
        implemented_but_not_run=True,
        notes="offline unit manifest",
    )

    validate_tokenizer_manifest(manifest, Path.cwd())

    assert manifest["model_path"] == ""
    assert manifest["vocab_path"] == ""
    assert manifest["implemented_but_not_run"] is True
