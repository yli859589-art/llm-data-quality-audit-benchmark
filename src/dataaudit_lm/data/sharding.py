from __future__ import annotations

from collections import defaultdict

from dataaudit_lm.data.records import DataRecord
from dataaudit_lm.integrity.hashing import stable_hash_int


def deterministic_shards(records: list[DataRecord], *, shard_count: int) -> dict[str, list[DataRecord]]:
    if shard_count <= 0:
        raise ValueError("shard_count must be positive")
    shards: dict[str, list[DataRecord]] = defaultdict(list)
    for record in records:
        index = stable_hash_int(record.record_id) % shard_count
        shards[f"shard_{index:05d}"].append(record)
    return {
        name: sorted(items, key=lambda item: item.record_id)
        for name, items in sorted(shards.items())
    }
