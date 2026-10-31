"""Non-destructive train/validation/test duplicate audit."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Iterable

from filters_v2.persistent_minhash import PersistentMinHashIndex


def audit_split_duplicates(
    records: Iterable[dict[str, Any]], index: PersistentMinHashIndex, *, threshold: float = 0.9
) -> dict[str, Any]:
    exact: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    near_pairs: list[dict[str, str]] = []
    id_conflicts: list[str] = []
    seen_ids: set[str] = set()
    docs = tokens = 0
    for row in records:
        doc_id, split, text = str(row["id"]), str(row["split"]), str(row.get("text", ""))
        docs += 1
        tokens += int(row.get("gpt2_tokens", len(text.split())))
        if doc_id in seen_ids:
            id_conflicts.append(doc_id)
        seen_ids.add(doc_id)
        digest = hashlib.sha256(" ".join(text.casefold().split()).encode()).hexdigest()
        exact[digest].append((doc_id, split, int(row.get("gpt2_tokens", len(text.split())))))
        for prior in index.confirmed_duplicates(text, threshold):
            near_pairs.append({"doc_id": doc_id, "duplicate_of": prior, "split": split})
        index.add(doc_id, text, split)
    exact_cross = [group for group in exact.values() if len({item[1] for item in group}) > 1]
    return {
        "mode": "audit_only_no_deletion",
        "documents": docs,
        "tokens": tokens,
        "id_conflicts": sorted(set(id_conflicts)),
        "exact_cross_split_clusters": exact_cross,
        "near_duplicate_pairs": near_pairs,
        "exact_cross_split_documents": sum(len(group) for group in exact_cross),
        "near_duplicate_pair_count": len(near_pairs),
    }
