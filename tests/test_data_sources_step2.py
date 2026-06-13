from __future__ import annotations

from pathlib import Path

from data_sources.base import DatasetSourceConfig
from data_sources.load_fineweb import build_source as build_fineweb
from data_sources.load_openwebtext import build_source as build_openwebtext
from data_sources.load_wikitext2 import build_source as build_wikitext2
from data_sources.validation import validate_manifest


def _config(dataset_name: str, scope: str, output: Path, manifest: Path) -> DatasetSourceConfig:
    return DatasetSourceConfig(
        dataset_name=dataset_name,
        dataset_version="unit",
        split="train",
        source_kind="fixture" if scope == "smoke" else "optional_remote",
        token_budget="10K",
        sampling_seed=42,
        allow_fallback=False,
        streaming=False,
        cache_dir="",
        output_path=str(output),
        manifest_path=str(manifest),
        license_note="unit",
        scope=scope,
        smoke_only=scope == "smoke",
        upstream_url_or_id="unit",
    )


def test_wikitext2_smoke_source_marks_fixture_records(tmp_path: Path) -> None:
    source = build_wikitext2(
        _config("WikiText-2", "smoke", tmp_path / "train.jsonl", tmp_path / "manifest.json"),
        root=Path.cwd(),
    )
    records = list(source.iter_records())
    assert records
    assert all(record.metadata["smoke_only"] is True for record in records)


def test_openwebtext_protocol_can_read_existing_streaming_cache() -> None:
    config = DatasetSourceConfig(
        dataset_name="OpenWebText",
        dataset_version="unit",
        split="train",
        source_kind="local",
        token_budget="1K",
        sampling_seed=42,
        allow_fallback=False,
        streaming=False,
        cache_dir="artifacts/data/openwebtext_streaming/splits",
        output_path="unused.jsonl",
        manifest_path="unused_manifest.json",
        license_note="unit",
        scope="sample",
        upstream_url_or_id="openwebtext",
    )
    source = build_openwebtext(config, root=Path.cwd())
    records = list(source.iter_records())
    assert records
    assert records[0].source == "openwebtext"


def test_fineweb_implemented_but_not_run_manifest_has_no_output(tmp_path: Path) -> None:
    source = build_fineweb(
        _config("FineWeb", "implemented_but_not_run", tmp_path / "fake.jsonl", tmp_path / "manifest.json"),
        root=Path.cwd(),
    )
    manifest = source.prepare()
    validate_manifest(manifest, Path.cwd())
    assert manifest["implemented_but_not_run"] is True
    assert manifest["output_path"] == ""
    assert not (tmp_path / "fake.jsonl").exists()
