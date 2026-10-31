from __future__ import annotations

import json
from pathlib import Path

import pytest

from artifacts_v2.legacy_integrity import legacy_exception
from training_v2.manifest import sha256_file
from training_v2.validation import TrainingManifestError, validate_training_manifest


def test_repo_smoke_training_manifest_hashes_validate() -> None:
    manifest_path = Path("artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert legacy_exception(manifest_path, Path.cwd()) is not None
    with pytest.raises(TrainingManifestError, match="dataset_manifest_hash"):
        validate_training_manifest(manifest, Path.cwd())

    assert manifest["manifest_version"] == "step5.training_manifest.v1"
    assert manifest["scope"] == "smoke"
    assert manifest["smoke_only"] is True
    assert manifest["checkpoint_manifest_path"].endswith("checkpoint_manifest.json")


def test_training_manifest_validation_catches_metric_hash_mismatch() -> None:
    manifest_path = Path("artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for path_field, hash_field in [
        ("dataset_manifest_path", "dataset_manifest_hash"),
        ("tokenizer_manifest_path", "tokenizer_manifest_hash"),
        ("filter_manifest_path", "filter_manifest_hash"),
        ("checkpoint_path", "checkpoint_hash"),
        ("checkpoint_manifest_path", "checkpoint_manifest_hash"),
    ]:
        if manifest[path_field]:
            manifest[hash_field] = sha256_file(Path(manifest[path_field]))
    manifest["metrics_hash"] = "0" * 64

    with pytest.raises(TrainingManifestError, match="metrics_hash"):
        validate_training_manifest(manifest, Path.cwd())
