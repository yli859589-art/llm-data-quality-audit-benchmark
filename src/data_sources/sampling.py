from __future__ import annotations

import json
import random
from collections.abc import Iterable
from pathlib import Path

from .records import DatasetRecord


def deterministic_order(records: Iterable[DatasetRecord], *, seed: int, shuffle: bool) -> list[DatasetRecord]:
    ordered = list(records)
    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(ordered)
    return ordered


def read_jsonl_records(path: Path, *, dataset_name: str, split: str, text_field: str = "text") -> list[DatasetRecord]:
    records: list[DatasetRecord] = []
    if not path.exists():
        return records
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        row = json.loads(line)
        text = row.get(text_field)
        if not isinstance(text, str) or not text.strip():
            continue
        doc_id = str(row.get("doc_id") or row.get("id") or f"{dataset_name}-{split}-{index}")
        metadata = dict(row.get("metadata") or {})
        records.append(
            DatasetRecord(
                doc_id=doc_id,
                text=text.strip(),
                source=dataset_name,
                split=split,
                metadata=metadata,
            )
        )
    return records


def write_jsonl_records(path: Path, records: Iterable[DatasetRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record.to_json_obj(), ensure_ascii=False, sort_keys=True) + "\n")
