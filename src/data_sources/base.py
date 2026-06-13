from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from .manifest import manifest_for_records, write_manifest
from .records import DatasetRecord
from .sampling import write_jsonl_records
from .token_budget import estimate_text_tokens, select_records_to_budget
from .validation import validate_manifest


class DatasetSplit(str, Enum):
    TRAIN = "train"
    VALIDATION = "validation"
    DEV = "dev"
    TEST = "test"


@dataclass(frozen=True)
class DatasetSourceConfig:
    dataset_name: str
    dataset_version: str
    split: str
    source_kind: str
    token_budget: str | int | None
    sampling_seed: int
    allow_fallback: bool
    streaming: bool
    cache_dir: str
    output_path: str
    manifest_path: str
    license_note: str
    scope: str = "sample"
    shuffle: bool = False
    token_counter_type: str = "whitespace"
    smoke_only: bool = False
    fallback_used: bool = False
    upstream_url_or_id: str = ""
    notes: str = ""


class DatasetSource:
    loader_name = "dataset_source_base"
    loader_version = "step2.v1"

    def __init__(self, config: DatasetSourceConfig, root: Path | None = None) -> None:
        self.config = config
        self.root = root or Path.cwd()

    def iter_records(self) -> Iterable[DatasetRecord]:
        raise NotImplementedError

    def estimate_tokens(self, records: Iterable[DatasetRecord] | None = None) -> int:
        source_records = list(self.iter_records() if records is None else records)
        return sum(estimate_text_tokens(record.text, self.config.token_counter_type) for record in source_records)

    def write_jsonl(self, records: Iterable[DatasetRecord], output_path: str | Path | None = None) -> Path:
        path = Path(output_path or self.config.output_path)
        if not path.is_absolute():
            path = self.root / path
        write_jsonl_records(path, records)
        return path

    def write_manifest(
        self,
        *,
        records: list[DatasetRecord],
        output_path: Path | None,
        manifest_path: str | Path | None = None,
        implemented_but_not_run: bool = False,
        notes: str | None = None,
    ) -> dict[str, object]:
        path = Path(manifest_path or self.config.manifest_path)
        if not path.is_absolute():
            path = self.root / path
        manifest = manifest_for_records(
            root=self.root,
            dataset_name=self.config.dataset_name,
            dataset_version=self.config.dataset_version,
            split=self.config.split,
            source_kind=self.config.source_kind,
            scope=self.config.scope,
            token_budget_requested=self.config.token_budget,
            records=records,
            token_counter_type=self.config.token_counter_type,
            sampling_seed=self.config.sampling_seed,
            shuffle=self.config.shuffle,
            allow_fallback=False if self.config.scope in {"main", "heavy"} else self.config.allow_fallback,
            fallback_used=self.config.fallback_used,
            smoke_only=self.config.smoke_only,
            implemented_but_not_run=implemented_but_not_run,
            output_path=output_path,
            license_note=self.config.license_note,
            loader_name=self.loader_name,
            loader_version=self.loader_version,
            upstream_url_or_id=self.config.upstream_url_or_id,
            notes=notes if notes is not None else self.config.notes,
        )
        validate_manifest(manifest, self.root)
        write_manifest(path, manifest)
        return manifest

    def prepare(self) -> dict[str, object]:
        if self.config.scope == "implemented_but_not_run":
            return self.write_manifest(
                records=[],
                output_path=None,
                implemented_but_not_run=True,
                notes=self.config.notes or "Protocol is implemented, but no real data was prepared in Step 2.",
            )
        records = select_records_to_budget(
            self.iter_records(),
            token_budget=self.config.token_budget,
            seed=self.config.sampling_seed,
            shuffle=self.config.shuffle,
            token_counter=self.config.token_counter_type,
        )
        output_path = self.write_jsonl(records)
        return self.write_manifest(records=records, output_path=output_path)


class NotPrepared(RuntimeError):
    pass


class OptionalDatasetUnavailable(NotPrepared):
    pass
