from __future__ import annotations

from pathlib import Path

import pytest

from data_sources.manifest import create_manifest
from data_sources.validation import DatasetManifestError, validate_manifest


def _manifest(**overrides):
    base = create_manifest(
        root=Path.cwd(),
        dataset_name="unit",
        dataset_version="v1",
        split="train",
        source_kind="local",
        scope="main",
        token_budget_requested="10K",
        actual_estimated_tokens=0,
        token_counter_type="whitespace",
        num_documents=0,
        sampling_seed=42,
        shuffle=False,
        allow_fallback=False,
        fallback_used=False,
        smoke_only=False,
        implemented_but_not_run=False,
        output_path=None,
        license_note="unit",
        loader_name="unit",
        loader_version="step2.v1",
        upstream_url_or_id="unit",
    )
    base.update(overrides)
    return base


def test_main_scope_rejects_fallback() -> None:
    with pytest.raises(DatasetManifestError):
        validate_manifest(_manifest(allow_fallback=True), Path.cwd())
    with pytest.raises(DatasetManifestError):
        validate_manifest(_manifest(fallback_used=True), Path.cwd())


def test_smoke_scope_requires_smoke_only() -> None:
    with pytest.raises(DatasetManifestError):
        validate_manifest(_manifest(scope="smoke", source_kind="fixture", smoke_only=False), Path.cwd())


def test_implemented_but_not_run_cannot_claim_output() -> None:
    with pytest.raises(DatasetManifestError):
        validate_manifest(
            _manifest(
                scope="implemented_but_not_run",
                source_kind="optional_remote",
                implemented_but_not_run=True,
                output_path="artifacts/data_step2/fake/train.jsonl",
            ),
            Path.cwd(),
        )
