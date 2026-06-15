from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.integrity.hashing import sha256_json


@dataclass(frozen=True)
class FilterDecision:
    record_id: str
    kept: bool
    reason: str
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FilterResult:
    method_name: str
    input_count: int
    kept_records: list[DataRecord]
    decisions: list[FilterDecision]
    manifest: dict[str, Any]

    @property
    def kept_ids(self) -> list[str]:
        return [record.record_id for record in self.kept_records]

    @property
    def kept_tokens(self) -> int:
        return sum(record.token_count for record in self.kept_records)


def build_filter_manifest(
    *,
    method_name: str,
    records: list[DataRecord],
    decisions: list[FilterDecision],
    parameters: dict[str, Any],
    notes: str = "",
) -> dict[str, Any]:
    kept = [decision.record_id for decision in decisions if decision.kept]
    rejected = [decision.record_id for decision in decisions if not decision.kept]
    payload: dict[str, Any] = {
        "manifest_version": "dataaudit_lm_filter_manifest_v1",
        "method_name": method_name,
        "parameters": parameters,
        "input_count": len(records),
        "kept_count": len(kept),
        "rejected_count": len(rejected),
        "input_tokens": sum(record.token_count for record in records),
        "kept_tokens": sum(
            record.token_count for record in records if record.record_id in set(kept)
        ),
        "selected_ids": kept,
        "rejected_ids": rejected,
        "decision_hash": sha256_json([asdict(decision) for decision in decisions]),
        "notes": notes,
    }
    payload["manifest_hash"] = sha256_json(payload)
    return payload
