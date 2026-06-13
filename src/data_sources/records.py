from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DatasetRecord:
    doc_id: str
    text: str
    source: str
    split: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json_obj(self) -> dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "text": self.text,
            "source": self.source,
            "split": self.split,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_json_obj(cls, value: dict[str, Any]) -> "DatasetRecord":
        return cls(
            doc_id=str(value["doc_id"]),
            text=str(value["text"]),
            source=str(value["source"]),
            split=str(value["split"]),
            metadata=dict(value.get("metadata") or {}),
        )
