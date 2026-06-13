from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .base import DatasetSource, DatasetSourceConfig, OptionalDatasetUnavailable
from .records import DatasetRecord
from .sampling import read_jsonl_records


class FineWebSource(DatasetSource):
    loader_name = "fineweb_step2_protocol_loader"

    def iter_records(self) -> Iterable[DatasetRecord]:
        split = self.config.split
        if self.config.scope == "smoke" or self.config.source_kind == "fixture":
            yield DatasetRecord(
                doc_id=f"fineweb-smoke-{split}-0",
                text="FineWeb Step 2 smoke fixture for offline protocol validation.",
                source="fineweb",
                split=split,
                metadata={"smoke_only": True, "fixture": "step2_fineweb_smoke"},
            )
            return
        if self.config.cache_dir:
            path = self.root / self.config.cache_dir / f"{split}.jsonl"
            records = read_jsonl_records(path, dataset_name="fineweb", split=split)
            if records:
                for record in records:
                    yield record
                return
        raise OptionalDatasetUnavailable(
            "FineWeb is protocol-only in Step 2 unless a local JSONL cache is provided."
        )


def build_source(config: DatasetSourceConfig, root: Path | None = None) -> FineWebSource:
    return FineWebSource(config, root=root)
