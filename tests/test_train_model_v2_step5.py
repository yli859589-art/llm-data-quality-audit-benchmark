from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from models_v2.config import ModelConfig
from tokenization.base import TokenizerConfig
from tokenization.bpe_tokenizer import LightweightBPETokenizer
from tokenization.manifest import create_tokenizer_manifest, write_tokenizer_manifest
from training_v2.config import TrainingConfig
from training_v2.trainer import run_training
from training_v2.validation import validate_training_manifest


def _make_temp_bpe_manifest(root: Path) -> Path:
    dataset = root / "train.jsonl"
    texts = ["alpha beta gamma alpha", "beta gamma delta beta", "alpha delta gamma beta"]
    dataset.write_text(
        "\n".join(json.dumps({"text": text}) for text in texts) + "\n",
        encoding="utf-8",
    )
    (root / "data_manifest.json").write_text(
        json.dumps({"token_counter_type": "unit_test"}, sort_keys=True),
        encoding="utf-8",
    )
    config = TokenizerConfig(
        tokenizer_name="unit_bpe",
        tokenizer_type="lightweight_bpe_smoke",
        vocab_size=64,
        training_data_path="train.jsonl",
        training_scope="smoke",
        seed=7,
        normalization="identity",
        model_path="tokenizer.json",
        vocab_path="",
        manifest_path="tokenizer_manifest.json",
        fallback_allowed=True,
        smoke_only=True,
    )
    tokenizer = LightweightBPETokenizer(config).train(texts)
    tokenizer.save(root / "tokenizer.json")
    manifest = create_tokenizer_manifest(
        tokenizer=tokenizer,
        root=root,
        tokenizer_name="unit_bpe",
        tokenizer_type="lightweight_bpe_smoke",
        scope="smoke",
        level3_mainline=False,
        vocab_size_requested=64,
        vocab_size_actual=tokenizer.vocab_size,
        training_data_path="train.jsonl",
        training_scope="smoke",
        seed=7,
        normalization="identity",
        model_path="tokenizer.json",
        vocab_path="",
        fallback_used=True,
        fallback_type="lightweight_bpe_smoke",
        smoke_only=True,
        notes="unit-test smoke tokenizer",
    )
    manifest_path = root / "tokenizer_manifest.json"
    write_tokenizer_manifest(manifest_path, manifest)
    return manifest_path


def test_train_model_v2_help_entrypoint_is_available() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/train_model_v2.py", "--help"],
        cwd=Path.cwd(),
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Run Step 5 tokenizer-aware smoke training" in result.stdout


def test_run_training_writes_metrics_manifest_and_checkpoint_manifest(tmp_path: Path) -> None:
    _make_temp_bpe_manifest(tmp_path)
    model_config = ModelConfig.from_mapping(
        {
            "model_name": "unit_tiny_bpe",
            "model_family": "decoder_lm",
            "vocab_size": 64,
            "context_length": 4,
            "num_layers": 1,
            "hidden_size": 8,
            "num_heads": 2,
            "dropout": 0.0,
            "tie_embeddings": True,
            "scale_class": "tiny_smoke",
        }
    )
    training_config = TrainingConfig.from_mapping(
        {
            "experiment_name": "unit_step5_smoke",
            "dataset_path": "train.jsonl",
            "dataset_manifest_path": "data_manifest.json",
            "tokenizer_manifest_path": "tokenizer_manifest.json",
            "filter_manifest_path": "",
            "model_config_path": "model_config.json",
            "output_dir": "training_out",
            "scope": "smoke",
            "seed": 11,
            "max_steps": 1,
            "batch_size": 2,
            "learning_rate": 0.001,
            "weight_decay": 0.0,
            "warmup_steps": 0,
            "gradient_clip": 1.0,
            "eval_interval": 1,
            "save_checkpoint": True,
            "device": "cpu",
            "precision": "float32",
            "resume_from": "",
            "smoke_only": True,
        }
    )

    result = run_training(training_config=training_config, model_config=model_config, root=tmp_path)
    manifest = result["manifest"]

    validate_training_manifest(manifest, tmp_path)
    assert (tmp_path / manifest["metrics_path"]).exists()
    assert (tmp_path / manifest["checkpoint_path"]).exists()
    assert (tmp_path / manifest["checkpoint_manifest_path"]).exists()
    assert manifest["scope"] == "smoke"
    assert manifest["smoke_only"] is True
    assert manifest["tokens_seen"] == 8
