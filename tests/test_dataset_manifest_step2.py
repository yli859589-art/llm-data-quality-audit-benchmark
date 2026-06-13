from __future__ import annotations

from pathlib import Path

from data_sources.manifest import manifest_for_records
from data_sources.records import DatasetRecord
from data_sources.sampling import write_jsonl_records
from data_sources.validation import validate_manifest, validate_output_hash


def test_manifest_schema_and_hash_validation(tmp_path: Path) -> None:
    records = [DatasetRecord("doc-1", "alpha beta", "unit", "train", {})]
    output = tmp_path / "train.jsonl"
    write_jsonl_records(output, records)
    manifest = manifest_for_records(
        root=Path.cwd(),
        dataset_name="unit",
        dataset_version="v1",
        split="train",
        source_kind="fixture",
        scope="smoke",
        token_budget_requested="10K",
        records=records,
        token_counter_type="whitespace",
        sampling_seed=42,
        shuffle=False,
        allow_fallback=True,
        fallback_used=False,
        smoke_only=True,
        implemented_but_not_run=False,
        output_path=output,
        license_note="unit",
        loader_name="unit_loader",
        loader_version="step2.v1",
        upstream_url_or_id="unit",
    )
    validate_manifest(manifest, Path.cwd())
    validate_output_hash(manifest, Path.cwd())
    assert manifest["manifest_version"] == "step2.dataset_manifest.v1"
    assert manifest["data_hash"]


def test_manifest_records_proxy_token_counter_type(tmp_path: Path) -> None:
    records = [DatasetRecord("doc-1", "alpha beta gamma", "unit", "train", {})]
    output = tmp_path / "train.jsonl"
    write_jsonl_records(output, records)
    manifest = manifest_for_records(
        root=Path.cwd(),
        dataset_name="unit",
        dataset_version="v1",
        split="train",
        source_kind="fixture",
        scope="smoke",
        token_budget_requested="10K",
        records=records,
        token_counter_type="whitespace",
        sampling_seed=42,
        shuffle=False,
        allow_fallback=True,
        fallback_used=False,
        smoke_only=True,
        implemented_but_not_run=False,
        output_path=output,
        license_note="unit",
        loader_name="unit_loader",
        loader_version="step2.v1",
        upstream_url_or_id="unit",
    )
    assert manifest["token_counter_type"] == "whitespace"
    assert manifest["actual_estimated_tokens"] == 3
