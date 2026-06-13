from __future__ import annotations

import json
from pathlib import Path

import pytest

from training_v2.validation import TrainingManifestError, validate_training_manifest


def test_repo_smoke_training_manifest_hashes_validate() -> None:
    manifest_path = Path("artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    validate_training_manifest(manifest, Path.cwd())

    assert manifest["manifest_version"] == "step5.training_manifest.v1"
    assert manifest["scope"] == "smoke"
    assert manifest["smoke_only"] is True
    assert manifest["checkpoint_manifest_path"].endswith("checkpoint_manifest.json")


def test_training_manifest_validation_catches_metric_hash_mismatch() -> None:
    manifest_path = Path("artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["metrics_hash"] = "0" * 64

    with pytest.raises(TrainingManifestError, match="metrics_hash"):
        validate_training_manifest(manifest, Path.cwd())
