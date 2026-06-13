from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .base import DatasetSource, DatasetSourceConfig, OptionalDatasetUnavailable
from .records import DatasetRecord
from .sampling import read_jsonl_records


class PileSubsetSource(DatasetSource):
    loader_name = "pile_subset_step2_protocol_loader"

    def iter_records(self) -> Iterable[DatasetRecord]:
        split = self.config.split
        if self.config.scope == "smoke" or self.config.source_kind == "fixture":
            yield DatasetRecord(
                doc_id=f"pile-smoke-{split}-0",
                text="Pile subset Step 2 smoke fixture for offline protocol validation.",
                source="pile",
                split=split,
                metadata={"smoke_only": True, "fixture": "step2_pile_smoke"},
            )
            return
        if self.config.cache_dir:
            path = self.root / self.config.cache_dir / f"{split}.jsonl"
            records = read_jsonl_records(path, dataset_name="pile", split=split)
            if records:
                for record in records:
                    yield record
                return
        raise OptionalDatasetUnavailable(
            "Pile subset is optional/protocol-only in Step 2 unless a local JSONL cache is provided."
        )


def build_source(config: DatasetSourceConfig, root: Path | None = None) -> PileSubsetSource:
    return PileSubsetSource(config, root=root)
