from __future__ import annotations

import random
import re
from collections.abc import Callable, Iterable
from typing import TypeVar

from .records import DatasetRecord

T = TypeVar("T", bound=DatasetRecord)

_BUDGET_RE = re.compile(r"^(\d+)([kmb])?$", re.IGNORECASE)
_MULTIPLIERS = {"k": 1_000, "m": 1_000_000, "b": 1_000_000_000}


def parse_token_budget(value: str | int | None) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        if value < 0:
            raise ValueError("token budget must be non-negative")
        return value
    cleaned = str(value).strip()
    if cleaned.casefold() == "full":
        return None
    match = _BUDGET_RE.match(cleaned)
    if not match:
        raise ValueError(f"unsupported token budget: {value}")
    amount = int(match.group(1))
    suffix = match.group(2)
    return amount * _MULTIPLIERS.get(suffix.casefold(), 1) if suffix else amount


def estimate_text_tokens(text: str, token_counter_type: str = "whitespace") -> int:
    if token_counter_type == "whitespace":
        return len(text.split())
    if token_counter_type == "character":
        return len(text)
    if token_counter_type in {"unknown", "future_bpe"}:
        return 0
    raise ValueError(f"unsupported token_counter_type: {token_counter_type}")


def _counter_fn(token_counter: str | Callable[[str], int]) -> Callable[[str], int]:
    if callable(token_counter):
        return token_counter
    return lambda text: estimate_text_tokens(text, token_counter)


def select_records_to_budget(
    records: Iterable[T],
    token_budget: str | int | None,
    seed: int = 13,
    shuffle: bool = False,
    token_counter: str | Callable[[str], int] = "whitespace",
) -> list[T]:
    numeric_budget = parse_token_budget(token_budget)
    candidates = list(records)
    if shuffle:
        rng = random.Random(seed)
        rng.shuffle(candidates)
    if numeric_budget is None:
        return candidates
    counter = _counter_fn(token_counter)
    selected: list[T] = []
    total = 0
    for record in candidates:
        count = counter(record.text)
        if selected and total + count > numeric_budget:
            break
        selected.append(record)
        total += count
        if total >= numeric_budget:
            break
    return selected
