from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from course_project_suite.llm_benchmark.config import load_yaml_config

from .hf_loaders import load_huggingface_texts
from .token_counting import truncate_by_budget


@dataclass(frozen=True)
class DataDocument:
    text: str
    dataset_key: str
    source_id: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class CorpusLoadResult:
    dataset_key: str
    documents: list[str]
    metadata: dict[str, Any]


def _read_local_text(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]
    if len(chunks) <= 1:
        chunks = [line.strip() for line in text.splitlines() if line.strip()]
    return chunks


def _read_local_jsonl(path: Path, text_field: str) -> list[str]:
    documents: list[str] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        value = row.get(text_field)
        if not isinstance(value, str):
            raise ValueError(f"{path}:{line_number} missing text field `{text_field}`")
        if value.strip():
            documents.append(value.strip())
    return documents


def _load_fallback(config: dict[str, Any], root: Path, reason: str) -> CorpusLoadResult:
    fixture = config.get("fallback_fixture")
    if not fixture or not config.get("allow_fallback", False):
        raise RuntimeError(reason)
    fallback_path = root / fixture
    documents = _read_local_text(fallback_path)
    documents = truncate_by_budget(
        documents,
        max_documents=config.get("max_documents"),
        max_tokens=config.get("max_tokens"),
        max_bytes=config.get("max_bytes"),
    )
    metadata = _metadata_from_config(config)
    metadata.update(
        {
            "provider": "local_fallback_fixture",
            "source": fixture,
            "used_fallback": True,
            "fallback_reason": reason,
        }
    )
    return CorpusLoadResult(str(config["dataset_key"]), documents, metadata)


def _metadata_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_name": config.get("dataset_name", config.get("dataset_key")),
        "provider": config.get("provider"),
        "source": config.get("hf_dataset") or config.get("path"),
        "license_note": config.get("license_note", "verify upstream license before use"),
        "required_real_data": bool(config.get("required_real_data", False)),
        "is_smoke": bool(config.get("is_smoke", False)),
        "streaming": bool(config.get("streaming", False)),
        "seed": config.get("seed", 13),
        "used_fallback": False,
        "fallback_reason": "",
    }


def load_documents_from_config(config_path: str | Path, *, root: Path) -> CorpusLoadResult:
    config = load_yaml_config(config_path)
    provider = str(config.get("provider", "local_text"))
    dataset_key = str(config["dataset_key"])

    try:
        if provider == "local_text":
            documents = _read_local_text(root / str(config["path"]))
        elif provider == "local_jsonl":
            documents = _read_local_jsonl(
                root / str(config["path"]),
                str(config.get("text_field", "text")),
            )
        elif provider == "huggingface":
            if config.get("is_smoke") and config.get("prefer_fallback_when_smoke", True):
                return _load_fallback(
                    config,
                    root,
                    "smoke config intentionally uses the local fixture for offline speed",
                )
            documents = load_huggingface_texts(config, root)
        else:
            raise ValueError(f"Unsupported data provider: {provider}")
    except Exception as exc:
        reason = f"{provider} load failed for {dataset_key}: {exc}"
        if config.get("required_real_data") and not config.get("allow_fallback", False):
            raise RuntimeError(reason) from exc
        return _load_fallback(config, root, reason)

    documents = truncate_by_budget(
        documents,
        max_documents=config.get("max_documents"),
        max_tokens=config.get("max_tokens"),
        max_bytes=config.get("max_bytes"),
    )
    if not documents:
        raise RuntimeError(f"{dataset_key} produced zero documents")
    return CorpusLoadResult(dataset_key, documents, _metadata_from_config(config))
