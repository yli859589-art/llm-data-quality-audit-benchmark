from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from dataaudit_lm.integrity.hashing import sha256_text


@dataclass(frozen=True)
class DataRecord:
    record_id: str
    source_row_id: str
    text: str
    content_sha256: str
    token_count: int
    source_dataset: str
    source_revision: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def estimate_gpt2_tokens(text: str) -> int:
    """A deterministic rehearsal token estimate; formal runs replace this with GPT-2 BPE."""
    return max(1, len(text.split()))


def make_record(
    *,
    record_id: str,
    source_row_id: str,
    text: str,
    source_dataset: str,
    source_revision: str,
    token_count: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> DataRecord:
    return DataRecord(
        record_id=record_id,
        source_row_id=source_row_id,
        text=text,
        content_sha256=sha256_text(text),
        token_count=estimate_gpt2_tokens(text) if token_count is None else int(token_count),
        source_dataset=source_dataset,
        source_revision=source_revision,
        metadata=dict(metadata or {}),
    )


def records_from_dicts(rows: Iterable[dict[str, Any]]) -> list[DataRecord]:
    records: list[DataRecord] = []
    for row in rows:
        text = str(row["text"])
        records.append(
            make_record(
                record_id=str(row["record_id"]),
                source_row_id=str(row.get("source_row_id", row["record_id"])),
                text=text,
                source_dataset=str(row.get("source_dataset", "unknown")),
                source_revision=str(row.get("source_revision", "unknown")),
                token_count=int(row.get("token_count") or estimate_gpt2_tokens(text)),
                metadata=dict(row.get("metadata") or {}),
            )
        )
    return records
