from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from data.real_corpora import _read_wikitext_articles

from .base import DatasetSource, DatasetSourceConfig, NotPrepared
from .records import DatasetRecord

_SMOKE_TEXTS = [
    "Step 2 WikiText smoke document about reproducible data manifests.",
    "A second tiny fixture keeps offline tests deterministic and smoke only.",
    "The smoke corpus is not main evidence and never enters main results.",
]


def _split_file_name(split: str) -> str:
    return "dev" if split == "validation" else split


class WikiText2Source(DatasetSource):
    loader_name = "wikitext2_step2_loader"

    def iter_records(self) -> Iterable[DatasetRecord]:
        split = _split_file_name(self.config.split)
        if self.config.scope == "smoke" or self.config.source_kind == "fixture":
            for index, text in enumerate(_SMOKE_TEXTS):
                yield DatasetRecord(
                    doc_id=f"wikitext2-smoke-{split}-{index}",
                    text=text,
                    source="wikitext2",
                    split=self.config.split,
                    metadata={"smoke_only": True, "fixture": "step2_wikitext2_smoke"},
                )
            return

        candidates = []
        if self.config.cache_dir:
            candidates.append(self.root / self.config.cache_dir / f"{split}.txt")
            candidates.append(self.root / self.config.cache_dir / f"{split}.jsonl")
        candidates.append(self.root / "data" / "real" / "wikitext2_raw" / f"{split}.txt")

        for path in candidates:
            if path.exists() and path.suffix == ".txt":
                for index, text in enumerate(_read_wikitext_articles(path)):
                    yield DatasetRecord(
                        doc_id=f"wikitext2-{split}-{index}",
                        text=text,
                        source="wikitext2",
                        split=self.config.split,
                        metadata={"source_path": path.relative_to(self.root).as_posix()},
                    )
                return
        raise NotPrepared(
            "WikiText-2 official split file is not prepared; expected data/real/wikitext2_raw/*.txt"
        )


def build_source(config: DatasetSourceConfig, root: Path | None = None) -> WikiText2Source:
    return WikiText2Source(config, root=root)
