from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .base import DatasetSource, DatasetSourceConfig, OptionalDatasetUnavailable
from .records import DatasetRecord
from .sampling import read_jsonl_records


class OpenWebTextSource(DatasetSource):
    loader_name = "openwebtext_step2_loader"

    def iter_records(self) -> Iterable[DatasetRecord]:
        split = "dev" if self.config.split == "validation" else self.config.split
        if self.config.scope == "smoke" or self.config.source_kind == "fixture":
            yield DatasetRecord(
                doc_id=f"openwebtext-smoke-{split}-0",
                text="OpenWebText Step 2 smoke fixture for offline interface tests.",
                source="openwebtext",
                split=self.config.split,
                metadata={"smoke_only": True, "fixture": "step2_openwebtext_smoke"},
            )
            return

        candidates = []
        if self.config.cache_dir:
            candidates.append(self.root / self.config.cache_dir / f"{split}.jsonl")
        candidates.append(self.root / "artifacts" / "data" / "openwebtext_streaming" / "splits" / f"{split}.jsonl")

        for path in candidates:
            records = read_jsonl_records(path, dataset_name="openwebtext", split=self.config.split)
            if records:
                for record in records:
                    yield record
                return
        raise OptionalDatasetUnavailable(
            "OpenWebText local streaming sample cache is unavailable; full upstream data is not prepared."
        )


def build_source(config: DatasetSourceConfig, root: Path | None = None) -> OpenWebTextSource:
    return OpenWebTextSource(config, root=root)
