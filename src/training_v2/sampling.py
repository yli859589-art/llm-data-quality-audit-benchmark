"""Deterministic, order-independent sampling of a streamed document pool."""
from __future__ import annotations

import hashlib
from collections.abc import Callable, Iterable
from typing import Any


def _priority(seed: int, document_id: str) -> str:
    return hashlib.sha256(f"{seed}:{document_id}".encode("utf-8")).hexdigest()


def build_document_token_pool(
    records: Callable[[], Iterable[dict[str, Any]]],
    encode: Callable[[str], list[int]],
    *,
    token_budget: int,
    seed: int,
    selected_ids: set[str] | None = None,
) -> tuple[list[int], dict[str, Any]]:
    """Select a reproducible document subset after scanning the whole pool.

    Only IDs, priorities, and token counts are held during the first pass. Text
    is re-streamed in the second pass only for selected documents, so this does
    not retain the corpus in memory and input file order cannot choose a prefix.
    """
    if token_budget <= 0:
        raise ValueError("token_budget must be positive")
    candidates: list[tuple[str, str, int]] = []
    pool_documents = pool_tokens = 0
    for row in records():
        document_id = str(row.get("id", ""))
        if not document_id or (selected_ids is not None and document_id not in selected_ids):
            continue
        count = int(row.get("gpt2_tokens", 0) or 0)
        if count <= 0:
            count = len(encode(str(row.get("text", ""))))
        if count <= 0:
            continue
        pool_documents += 1
        pool_tokens += count
        candidates.append((_priority(seed, document_id), document_id, count))
    candidates.sort()
    chosen: set[str] = set()
    chosen_order: list[str] = []
    chosen_tokens = 0
    for _, document_id, count in candidates:
        if count <= token_budget - chosen_tokens:
            chosen.add(document_id)
            chosen_order.append(document_id)
            chosen_tokens += count
    materialized: dict[str, list[int]] = {}
    for row in records():
        document_id = str(row.get("id", ""))
        if document_id not in chosen:
            continue
        ids = encode(str(row.get("text", "")))
        if len(ids) > token_budget:
            # Metadata may have been generated with a different tokenizer.
            continue
        materialized[document_id] = ids
    encoded: list[int] = []
    materialized_ids: list[str] = []
    for document_id in chosen_order:
        ids = materialized.get(document_id)
        if ids is None or len(encoded) + len(ids) > token_budget:
            continue
        encoded.extend(ids)
        materialized_ids.append(document_id)
    audit = {
        "sampling_strategy": "stable_sha256_document_budget_v1",
        "sampling_seed": seed,
        "source_pool_documents": pool_documents,
        "source_pool_tokens": pool_tokens,
        "selected_pool_documents": len(materialized_ids),
        "selected_pool_tokens": len(encoded),
        "unique_training_tokens_available": len(encoded),
        "token_budget": token_budget,
        "coverage_fraction_documents": len(materialized_ids) / max(1, pool_documents),
        "coverage_fraction_tokens": len(encoded) / max(1, pool_tokens),
        "selected_document_ids": materialized_ids,
        "input_order_independent": True,
    }
    return encoded, audit
