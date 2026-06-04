from __future__ import annotations

import re

TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)


def count_tokens(text: str) -> int:
    """Count approximate tokens with a deterministic regex tokenizer."""
    return len(TOKEN_RE.findall(text))


def count_document_tokens(documents: list[str]) -> list[int]:
    return [count_tokens(document) for document in documents]


def truncate_by_budget(
    documents: list[str],
    *,
    max_documents: int | None = None,
    max_tokens: int | None = None,
    max_bytes: int | None = None,
) -> list[str]:
    selected: list[str] = []
    total_tokens = 0
    total_bytes = 0
    for document in documents:
        if max_documents is not None and len(selected) >= max_documents:
            break
        document_tokens = count_tokens(document)
        document_bytes = len(document.encode("utf-8"))
        if max_tokens is not None and selected and total_tokens + document_tokens > max_tokens:
            break
        if max_bytes is not None and selected and total_bytes + document_bytes > max_bytes:
            break
        if max_tokens is not None and not selected and document_tokens > max_tokens:
            words = TOKEN_RE.findall(document)[:max_tokens]
            document = " ".join(words)
            document_tokens = count_tokens(document)
            document_bytes = len(document.encode("utf-8"))
        if max_bytes is not None and not selected and document_bytes > max_bytes:
            document = document.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore")
            document_tokens = count_tokens(document)
            document_bytes = len(document.encode("utf-8"))
        selected.append(document)
        total_tokens += document_tokens
        total_bytes += document_bytes
    return selected
