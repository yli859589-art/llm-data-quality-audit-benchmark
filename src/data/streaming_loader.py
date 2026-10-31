from __future__ import annotations

import json
from dataclasses import dataclass
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .token_counting import count_tokens


class StreamingDataError(RuntimeError):
    def __init__(self, status: str, reason: str) -> None:
        super().__init__(reason)
        self.status = status
        self.reason = reason


@dataclass(frozen=True)
class StreamingSample:
    documents: list[str]
    metadata: dict[str, Any]


def take_text_rows(
    rows: Iterable[dict[str, Any]],
    *,
    text_field: str,
    max_documents: int | None = None,
    max_tokens: int | None = None,
) -> list[str]:
    documents: list[str] = []
    token_total = 0
    for row in rows:
        value = row.get(text_field, "")
        if isinstance(value, str) and value.strip():
            text = value.strip()
            tokens = count_tokens(text)
            if max_tokens is not None and documents and token_total + tokens > max_tokens:
                break
            documents.append(text)
            token_total += tokens
        if max_documents is not None and len(documents) >= max_documents:
            break
    return documents


def classify_streaming_exception(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".casefold()
    if any(token in text for token in ["401", "403", "auth", "token", "permission", "gated"]):
        return "failed_due_to_auth"
    if any(token in text for token in ["no space", "disk", "quota"]):
        return "failed_due_to_disk"
    if any(
        token in text
        for token in [
            "connection",
            "connect",
            "timeout",
            "timed out",
            "network",
            "ssl",
            "proxy",
            "http",
            "remote",
            "couldn't reach",
            "could not reach",
        ]
    ):
        return "failed_due_to_network"
    return "failed_due_to_environment"


def load_huggingface_streaming_sample(config: dict[str, Any], root: Path) -> StreamingSample:
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise StreamingDataError(
            "failed_due_to_environment",
            "Hugging Face `datasets` is not installed.",
        ) from exc

    dataset_name = str(config["hf_dataset"])
    subset = config.get("hf_subset")
    split = str(config.get("hf_split", "train"))
    text_field = str(config.get("text_field", "text"))
    cache_dir = config.get("cache_dir")
    kwargs: dict[str, Any] = {"split": split, "streaming": True}
    if cache_dir:
        configured_cache = Path(str(cache_dir)).expanduser()
        cache_path = configured_cache if configured_cache.is_absolute() else root / configured_cache
        cache_path.mkdir(parents=True, exist_ok=True)
        kwargs["cache_dir"] = str(cache_path)
    if config.get("trust_remote_code") is not None:
        kwargs["trust_remote_code"] = bool(config.get("trust_remote_code"))

    try:
        rows = (
            load_dataset(dataset_name, str(subset), **kwargs)
            if subset
            else load_dataset(dataset_name, **kwargs)
        )
        seed = int(config.get("sample_seed", config.get("seed", 13)))
        buffer_size = int(config.get("shuffle_buffer_size", 1000))
        if hasattr(rows, "shuffle"):
            rows = rows.shuffle(seed=seed, buffer_size=buffer_size)
        documents = take_text_rows(
            rows,
            text_field=text_field,
            max_documents=config.get("max_documents"),
            max_tokens=config.get("max_tokens"),
        )
    except StreamingDataError:
        raise
    except Exception as exc:
        status = classify_streaming_exception(exc)
        raise StreamingDataError(status, f"{type(exc).__name__}: {exc}") from exc

    if not documents:
        raise StreamingDataError(
            "insufficient_streaming_sample",
            "Streaming source returned zero usable text documents.",
        )

    return StreamingSample(
        documents=documents,
        metadata={
            "provider": "huggingface_streaming",
            "source": dataset_name,
            "hf_subset": subset or "",
            "hf_split": split,
            "download_or_streaming_method": "huggingface datasets streaming",
            "streaming": True,
            "is_streaming_sample": True,
            "is_full_dataset": False,
            "sample_seed": int(config.get("sample_seed", config.get("seed", 13))),
        },
    )


def write_split_jsonl(output_dir: Path, splits: dict[str, list[str]]) -> dict[str, str]:
    split_dir = output_dir / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}
    for split_name, documents in splits.items():
        path = split_dir / f"{split_name}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for index, document in enumerate(documents):
                handle.write(json.dumps({"id": f"{split_name}-{index}", "text": document}) + "\n")
        paths[split_name] = path.as_posix()
    return paths


def read_split_jsonl(path: Path) -> list[str]:
    documents: list[str] = []
    if not path.exists():
        return documents
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        text = row.get("text", "")
        if isinstance(text, str) and text.strip():
            documents.append(text.strip())
    return documents
