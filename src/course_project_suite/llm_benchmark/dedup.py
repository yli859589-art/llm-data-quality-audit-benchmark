from __future__ import annotations

import hashlib

from .near_dedup import DeduplicationResult, near_deduplicate_jaccard


def exact_deduplicate(documents: list[str]) -> DeduplicationResult:
    seen: dict[str, int] = {}
    kept: list[str] = []
    clusters: dict[int, list[int]] = {}
    for index, document in enumerate(documents):
        digest = hashlib.sha1(document.encode("utf-8")).hexdigest()
        if digest in seen:
            clusters.setdefault(seen[digest], []).append(index)
        else:
            seen[digest] = index
            kept.append(document)
    cluster_rows = [
        {"representative_index": representative, "member_indices": members}
        for representative, members in clusters.items()
    ]
    return DeduplicationResult(kept, len(documents) - len(kept), cluster_rows)


def near_deduplicate(
    documents: list[str], threshold: float = 0.82, shingle_width: int = 3
) -> DeduplicationResult:
    """Compatibility wrapper for the small-corpus Jaccard reference baseline."""
    return near_deduplicate_jaccard(documents, threshold, shingle_width)
