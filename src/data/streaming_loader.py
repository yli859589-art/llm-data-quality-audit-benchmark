from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def take_text_rows(
    rows: Iterable[dict[str, Any]],
    *,
    text_field: str,
    max_documents: int | None = None,
) -> list[str]:
    documents: list[str] = []
    for row in rows:
        value = row.get(text_field, "")
        if isinstance(value, str) and value.strip():
            documents.append(value.strip())
        if max_documents is not None and len(documents) >= max_documents:
            break
    return documents
