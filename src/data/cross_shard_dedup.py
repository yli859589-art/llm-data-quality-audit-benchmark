"""Deterministic, persistent duplicate decisions across a set of corpus shards."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from data.scalable_pipeline import iter_records
from filters_v2.persistent_minhash import PersistentMinHashIndex


def index_cross_shard_records(
    shard_paths: Iterable[str], index: PersistentMinHashIndex, *, threshold: float = 0.9
) -> dict[str, Any]:
    """Build a durable cross-shard graph before emitting any keep/drop decision."""
    documents = 0
    for source_name in shard_paths:
        for row in iter_records(Path(source_name)):
            document_id = str(row.get("id", ""))
            if not document_id:
                raise ValueError(f"missing id in {source_name}")
            index.add_and_cluster(
                document_id,
                str(row.get("text", "")),
                str(row.get("split", "unspecified")),
                threshold=threshold,
            )
            documents += 1
        index.commit()  # shard-level durability; no full-corpus in-memory state
    representatives = index.cluster_representatives()
    clusters = len(set(representatives.values()))
    return {
        "documents": documents,
        "clusters": clusters,
        "duplicates": documents - clusters,
        "representative_rule": "lexicographically_smallest_document_id",
        "threshold": threshold,
    }


def write_dedup_decisions(index: PersistentMinHashIndex, output: Path) -> dict[str, int]:
    """Write one decision per indexed document in deterministic document-ID order."""
    output.parent.mkdir(parents=True, exist_ok=True)
    representatives = index.cluster_representatives()
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for document_id, representative in representatives.items():
            handle.write(
                json.dumps(
                    {
                        "id": document_id,
                        "keep": document_id == representative,
                        "representative_id": representative,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    return {
        "documents": len(representatives),
        "kept": sum(doc_id == rep for doc_id, rep in representatives.items()),
    }
