from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re


@dataclass(frozen=True)
class DeduplicationResult:
    documents: list[str]
    removed: int
    clusters: list[dict[str, object]]


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


def _shingles(text: str, width: int) -> set[str]:
    tokens = re.findall(r"\w+", text.casefold())
    if len(tokens) < width:
        return {" ".join(tokens)} if tokens else {""}
    return {" ".join(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}


def jaccard_similarity(left: str, right: str, shingle_width: int = 3) -> float:
    left_shingles = _shingles(left, shingle_width)
    right_shingles = _shingles(right, shingle_width)
    return len(left_shingles & right_shingles) / max(1, len(left_shingles | right_shingles))


def near_deduplicate(
    documents: list[str], threshold: float = 0.82, shingle_width: int = 3
) -> DeduplicationResult:
    """Remove later documents whose word-shingle Jaccard similarity crosses a threshold."""
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0, 1].")
    kept: list[str] = []
    kept_indices: list[int] = []
    clusters: list[dict[str, object]] = []
    for index, document in enumerate(documents):
        match: tuple[int, float] | None = None
        for representative, kept_document in zip(kept_indices, kept):
            similarity = jaccard_similarity(document, kept_document, shingle_width)
            if similarity >= threshold:
                match = (representative, similarity)
                break
        if match is None:
            kept.append(document)
            kept_indices.append(index)
        else:
            representative, similarity = match
            clusters.append(
                {
                    "representative_index": representative,
                    "member_index": index,
                    "jaccard_similarity": similarity,
                    "threshold": threshold,
                }
            )
    return DeduplicationResult(kept, len(documents) - len(kept), clusters)
