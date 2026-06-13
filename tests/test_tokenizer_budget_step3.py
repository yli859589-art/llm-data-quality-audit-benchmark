from __future__ import annotations

import json
from pathlib import Path

import pytest

from tokenization.base import TokenizerConfig
from tokenization.bpe_tokenizer import LightweightBPETokenizer
from tokenization.budget import (
    build_token_budget_report,
    compare_token_budgets_across_tokenizers,
    verify_budget_not_mislabeled,
)
from tokenization.manifest import create_tokenizer_manifest
from tokenization.validation import validate_budget_report


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


def _manifest_and_tokenizer(tmp_path: Path) -> tuple[dict[str, object], LightweightBPETokenizer, Path]:
    data_path = tmp_path / "train.jsonl"
    model_path = tmp_path / "tokenizer.json"
    vocab_path = tmp_path / "vocab.json"
    _write_jsonl(data_path)
    config = TokenizerConfig(
        tokenizer_name="bpe_budget_unit",
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
    manifest = create_tokenizer_manifest(
        tokenizer=tokenizer,
        root=Path.cwd(),
        tokenizer_name="bpe_budget_unit",
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
        notes="unit budget manifest",
    )
    return manifest, tokenizer, data_path


def test_tokenizer_budget_report_warns_about_proxy_counts(tmp_path: Path) -> None:
    manifest, _, data_path = _manifest_and_tokenizer(tmp_path)

    report = build_token_budget_report(
        data_path=data_path,
        tokenizer_manifest=manifest,
        root=Path.cwd(),
    )

    validate_budget_report(report)
    assert report["status"] == "passed"
    assert report["tokenizer_specific_token_count"] > 0
    assert report["proxy_vs_tokenizer_warning"]


def test_budget_type_mismatch_is_rejected(tmp_path: Path) -> None:
    manifest, _, _ = _manifest_and_tokenizer(tmp_path)
    manifest["training_scope"] = "step2_whitespace_proxy"

    with pytest.raises(ValueError):
        verify_budget_not_mislabeled(manifest, "lightweight_bpe_smoke")


def test_compare_token_budgets_across_tokenizers(tmp_path: Path) -> None:
    _, tokenizer, data_path = _manifest_and_tokenizer(tmp_path)

    counts = compare_token_budgets_across_tokenizers(data_path, {"bpe": tokenizer})

    assert counts["bpe"] > 0
