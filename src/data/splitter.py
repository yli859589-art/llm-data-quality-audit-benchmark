from __future__ import annotations

import hashlib
import random


def stable_document_id(text: str, *, salt: str = "") -> str:
    payload = f"{salt}\n{text}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def deterministic_split(
    documents: list[str],
    *,
    seed: int = 13,
    train_ratio: float = 0.8,
    dev_ratio: float = 0.1,
    test_ratio: float = 0.1,
) -> dict[str, list[str]]:
    total_ratio = train_ratio + dev_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-9:
        raise ValueError("split ratios must sum to 1.0")
    shuffled = list(documents)
    random.Random(seed).shuffle(shuffled)
    train_stop = int(len(shuffled) * train_ratio)
    dev_stop = train_stop + int(len(shuffled) * dev_ratio)
    if len(shuffled) >= 3 and dev_stop == train_stop:
        dev_stop = train_stop + 1
    return {
        "train": shuffled[:train_stop],
        "dev": shuffled[train_stop:dev_stop],
        "test": shuffled[dev_stop:],
    }


def split_hashes(splits: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        split_name: [stable_document_id(document) for document in split_docs]
        for split_name, split_docs in splits.items()
    }
