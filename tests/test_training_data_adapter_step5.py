from __future__ import annotations

import json
from pathlib import Path

from tokenization.char_tokenizer import CharTokenizer
from training_v2.data_adapter import build_tokenized_training_data


def test_bpe_data_adapter_loads_step2_jsonl_and_step3_manifest() -> None:
    data = build_tokenized_training_data(
        dataset_path="artifacts/data_step2/wikitext2_smoke/train.jsonl",
        dataset_manifest_path="artifacts/data_step2/wikitext2_smoke/data_manifest.json",
        tokenizer_manifest_path="artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json",
        context_length=8,
        root=Path.cwd(),
    )

    assert data.blocks_x.shape[1] == 8
    assert data.blocks_y.shape == data.blocks_x.shape
    assert data.summary["tokenizer_type"] == "lightweight_bpe_smoke"
    assert data.summary["encoded_tokens"] > 8
    assert "Step 2 whitespace proxy counts" in data.summary["token_budget_note"]


def test_char_legacy_data_adapter_path_works_with_temp_manifest(tmp_path: Path) -> None:
    dataset = tmp_path / "train.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps({"text": "hello world hello"}),
                json.dumps({"text": "world hello world"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    dataset_manifest = tmp_path / "data_manifest.json"
    dataset_manifest.write_text(
        json.dumps({"token_counter_type": "char_unit_test"}, sort_keys=True),
        encoding="utf-8",
    )
    tokenizer = CharTokenizer().train(["hello world"])
    vocab = tmp_path / "char_vocab.json"
    tokenizer.save(vocab)
    tokenizer_manifest = tmp_path / "tokenizer_manifest.json"
    tokenizer_manifest.write_text(
        json.dumps(
            {
                "tokenizer_type": "char",
                "vocab_path": "char_vocab.json",
                "tokenizer_hash": tokenizer.tokenizer_hash,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    data = build_tokenized_training_data(
        dataset_path="train.jsonl",
        dataset_manifest_path="data_manifest.json",
        tokenizer_manifest_path="tokenizer_manifest.json",
        context_length=4,
        root=tmp_path,
    )

    assert data.summary["tokenizer_type"] == "char"
    assert data.summary["dataset_token_counter_type"] == "char_unit_test"
    assert data.blocks_x.shape[1] == 4
