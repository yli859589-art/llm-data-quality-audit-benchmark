from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .base import DatasetSource, DatasetSourceConfig, OptionalDatasetUnavailable
from .records import DatasetRecord
from .sampling import read_jsonl_records


class C4EnglishSource(DatasetSource):
    loader_name = "c4_english_step2_loader"

    def iter_records(self) -> Iterable[DatasetRecord]:
        split = "dev" if self.config.split == "validation" else self.config.split
        if self.config.scope == "smoke" or self.config.source_kind == "fixture":
            yield DatasetRecord(
                doc_id=f"c4-smoke-{split}-0",
                text="C4 English Step 2 smoke fixture; not a full upstream C4 result.",
                source="c4",
                split=self.config.split,
                metadata={"smoke_only": True, "fixture": "step2_c4_smoke"},
            )
            return

        candidates = []
        if self.config.cache_dir:
            candidates.append(self.root / self.config.cache_dir / f"{split}.jsonl")
        candidates.append(self.root / "artifacts" / "data" / "c4_en_streaming" / "splits" / f"{split}.jsonl")

        for path in candidates:
            records = read_jsonl_records(path, dataset_name="c4", split=self.config.split)
            if records:
                for record in records:
                    yield record
                return
        raise OptionalDatasetUnavailable(
            "C4 local streaming sample cache is unavailable; full upstream C4 data is not prepared."
        )


def build_source(config: DatasetSourceConfig, root: Path | None = None) -> C4EnglishSource:
    return C4EnglishSource(config, root=root)
