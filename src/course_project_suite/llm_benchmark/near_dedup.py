from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class DeduplicationResult:
    documents: list[str]
    removed: int
    clusters: list[dict[str, object]]
    method: str = "jaccard"


def shingles(text: str, width: int = 3) -> set[str]:
    tokens = re.findall(r"\w+", text.casefold())
    if len(tokens) < width:
        return {" ".join(tokens)} if tokens else {""}
    return {" ".join(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}


def jaccard_similarity(left: str, right: str, shingle_width: int = 3) -> float:
    left_shingles = shingles(left, shingle_width)
    right_shingles = shingles(right, shingle_width)
    return len(left_shingles & right_shingles) / max(1, len(left_shingles | right_shingles))


def near_deduplicate_jaccard(
    documents: list[str], threshold: float = 0.82, shingle_width: int = 3
) -> DeduplicationResult:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0, 1].")
    kept: list[str] = []
    kept_indices: list[int] = []
    clusters: list[dict[str, object]] = []
    for index, document in enumerate(documents):
        match: tuple[int, float] | None = None
        for representative, kept_document in zip(kept_indices, kept, strict=True):
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
                    "similarity": similarity,
                    "threshold": threshold,
                    "method": "jaccard",
                }
            )
    return DeduplicationResult(kept, len(documents) - len(kept), clusters, "jaccard")


def _stable_hash(value: str, seed: int) -> int:
    digest = hashlib.blake2b(f"{seed}:{value}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def minhash_signature(
    text: str, *, num_perm: int = 64, shingle_width: int = 3, seed: int = 13
) -> tuple[int, ...]:
    text_shingles = shingles(text, shingle_width)
    signature = []
    for permutation in range(num_perm):
        signature.append(
            min(_stable_hash(shingle, seed + permutation * 1_000_003) for shingle in text_shingles)
        )
    return tuple(signature)


def _candidate_representatives(
    signature: tuple[int, ...],
    buckets: dict[tuple[int, tuple[int, ...]], list[int]],
    num_bands: int,
) -> set[int]:
    rows = max(1, len(signature) // num_bands)
    candidates: set[int] = set()
    for band in range(num_bands):
        start = band * rows
        stop = min(len(signature), start + rows)
        if start >= len(signature):
            break
        candidates.update(buckets[(band, signature[start:stop])])
    return candidates


def _add_signature_to_buckets(
    representative: int,
    signature: tuple[int, ...],
    buckets: dict[tuple[int, tuple[int, ...]], list[int]],
    num_bands: int,
) -> None:
    rows = max(1, len(signature) // num_bands)
    for band in range(num_bands):
        start = band * rows
        stop = min(len(signature), start + rows)
        if start >= len(signature):
            break
        buckets[(band, signature[start:stop])].append(representative)


def near_deduplicate_minhash_lsh(
    documents: list[str],
    *,
    threshold: float = 0.82,
    num_perm: int = 64,
    num_bands: int = 16,
    shingle_width: int = 3,
    seed: int = 13,
) -> DeduplicationResult:
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0, 1].")
    if num_perm <= 0 or num_bands <= 0:
        raise ValueError("num_perm and num_bands must be positive.")

    kept: list[str] = []
    kept_indices: list[int] = []
    kept_signatures: list[tuple[int, ...]] = []
    buckets: dict[tuple[int, tuple[int, ...]], list[int]] = defaultdict(list)
    clusters: list[dict[str, object]] = []

    for index, document in enumerate(documents):
        signature = minhash_signature(
            document, num_perm=num_perm, shingle_width=shingle_width, seed=seed
        )
        candidate_positions = _candidate_representatives(signature, buckets, num_bands)
        match: tuple[int, float, float] | None = None
        for position in sorted(candidate_positions):
            estimate = (
                sum(
                    left == right
                    for left, right in zip(signature, kept_signatures[position], strict=True)
                )
                / num_perm
            )
            similarity = jaccard_similarity(document, kept[position], shingle_width)
            if similarity >= threshold:
                match = (kept_indices[position], similarity, estimate)
                break
        if match is None:
            kept.append(document)
            kept_indices.append(index)
            kept_signatures.append(signature)
            _add_signature_to_buckets(len(kept) - 1, signature, buckets, num_bands)
        else:
            representative, similarity, estimate = match
            clusters.append(
                {
                    "representative_index": representative,
                    "member_index": index,
                    "similarity": similarity,
                    "minhash_similarity_estimate": estimate,
                    "threshold": threshold,
                    "method": "minhash_lsh",
                    "num_perm": num_perm,
                    "num_bands": num_bands,
                    "shingle_width": shingle_width,
                    "seed": seed,
                }
            )

    return DeduplicationResult(kept, len(documents) - len(kept), clusters, "minhash_lsh")


def near_deduplicate(
    documents: list[str],
    *,
    method: str = "jaccard",
    threshold: float = 0.82,
    num_perm: int = 64,
    num_bands: int = 16,
    shingle_width: int = 3,
    seed: int = 13,
) -> DeduplicationResult:
    if method == "jaccard":
        return near_deduplicate_jaccard(documents, threshold, shingle_width)
    if method == "minhash_lsh":
        return near_deduplicate_minhash_lsh(
            documents,
            threshold=threshold,
            num_perm=num_perm,
            num_bands=num_bands,
            shingle_width=shingle_width,
            seed=seed,
        )
    raise ValueError(f"Unsupported near-deduplication method: {method}")
