from __future__ import annotations

import hashlib
from collections import defaultdict

from .base import BaseFilter, FilterDecision, FilterInput
from .heuristics import jaccard


def _shingles(text: str, size: int) -> set[str]:
    words = text.casefold().split()
    if len(words) < size:
        return {" ".join(words)} if words else set()
    return {" ".join(words[index : index + size]) for index in range(len(words) - size + 1)}


def _signature(shingles: set[str], permutations: int, seed: int) -> tuple[int, ...]:
    if not shingles:
        return tuple(0 for _ in range(permutations))
    def value(shingle: str, permutation: int) -> int:
        return int.from_bytes(hashlib.blake2b(f"{seed}:{permutation}:{shingle}".encode("utf-8"), digest_size=8).digest(), "big")
    return tuple(min(value(shingle, permutation) for shingle in shingles) for permutation in range(permutations))


class MinHashNearDedupProxyFilter(BaseFilter):
    """Actual MinHash/LSH detector; the historical class name is compatible."""
    filter_type = "minhash_lsh_near_dedup_v1"
    proxy_used = False

    def filter(self, records: list[FilterInput]):
        threshold = float(self.config.params.get("similarity_threshold", 0.86))
        shingle_size = int(self.config.params.get("shingle_size", 3))
        permutations = int(self.config.params.get("num_permutations", 64))
        bands = int(self.config.params.get("bands", 16))
        if not 0 < threshold <= 1 or shingle_size < 1 or permutations < 4 or bands < 1 or permutations % bands:
            raise ValueError("invalid MinHash/LSH configuration")
        rows_per_band = permutations // bands
        buckets: dict[tuple[int, tuple[int, ...]], set[str]] = defaultdict(set)
        kept_shingles: dict[str, set[str]] = {}
        decisions_by_id: dict[str, FilterDecision] = {}
        comparisons = 0
        for record in sorted(records, key=lambda item: item.doc_id):
            current = _shingles(record.text, shingle_size)
            signature = _signature(current, permutations, int(self.config.seed))
            candidate_ids: set[str] = set()
            for band in range(bands):
                candidate_ids.update(buckets[(band, signature[band * rows_per_band : (band + 1) * rows_per_band])])
            matched_id, max_similarity = "", 0.0
            for candidate in sorted(candidate_ids):
                comparisons += 1
                similarity = jaccard(current, kept_shingles[candidate])
                if similarity > max_similarity:
                    matched_id, max_similarity = candidate, similarity
            keep = max_similarity < threshold
            if keep:
                kept_shingles[record.doc_id] = current
                for band in range(bands):
                    buckets[(band, signature[band * rows_per_band : (band + 1) * rows_per_band])].add(record.doc_id)
            decisions_by_id[record.doc_id] = FilterDecision(
                    doc_id=record.doc_id,
                    keep=keep,
                    score=1.0 - max_similarity,
                    reason="minhash_lsh_near_duplicate" if not keep else "minhash_lsh_cluster_representative",
                    metadata={
                        "component_scores": {"max_jaccard_similarity": max_similarity},
                        "duplicate_of": matched_id,
                        "algorithm": "MinHash+LSH candidate retrieval, exact shingle Jaccard confirmation",
                        "shingle_size": shingle_size, "num_permutations": permutations, "bands": bands, "seed": self.config.seed,
                    },
                )
        decisions = [decisions_by_id[record.doc_id] for record in records]
        result = self._result(records, decisions)
        result.summary.update({"algorithm": "minhash_lsh", "candidate_comparisons": comparisons, "all_pairs_avoided": True})
        self._last_records = list(records)
        self._last_result = result
        return result

    def score(self, record: FilterInput) -> FilterDecision:
        raise NotImplementedError("near dedup proxy uses batch-level comparisons")
