from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from dataaudit_lm.data.records import DataRecord, make_record


@dataclass(frozen=True)
class SourceSpec:
    dataset_repository: str
    config: str
    revision: str
    text_field: str = "text"


def ingest_rows_without_dedup(spec: SourceSpec, rows: Iterable[dict[str, object]]) -> list[DataRecord]:
    """Convert upstream rows to records while retaining true duplicate content."""
    records: list[DataRecord] = []
    for index, row in enumerate(rows):
        row_id = str(row.get("id", index))
        records.append(
            make_record(
                record_id=f"{spec.dataset_repository}:{spec.config}:{row_id}",
                source_row_id=row_id,
                text=str(row[spec.text_field]),
                source_dataset=spec.dataset_repository,
                source_revision=spec.revision,
                metadata={"config": spec.config, "row_index": index},
            )
        )
    return records
