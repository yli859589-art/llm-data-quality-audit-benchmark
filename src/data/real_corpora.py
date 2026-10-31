from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from course_project_suite.llm_benchmark.config import load_yaml_config

from .hf_loaders import load_huggingface_texts
from .streaming_loader import read_split_jsonl
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


def _download_text(url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists() and output_path.stat().st_size > 0:
        return
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            output_path.write_bytes(response.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} while downloading {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error while downloading {url}: {exc.reason}") from exc


def _read_text_documents(path: Path) -> list[str]:
    if "wikitext" in path.as_posix().casefold():
        return _read_wikitext_articles(path)
    documents = []
    for line in path.read_text(encoding="utf-8").splitlines():
        clean = line.strip()
        if clean:
            documents.append(clean)
    return documents


def _is_top_level_wikitext_heading(line: str) -> bool:
    return bool(re.match(r"^= [^=].* =\s*$", line))


def _read_wikitext_articles(path: Path) -> list[str]:
    documents: list[str] = []
    current: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_top_level_wikitext_heading(line) and current:
            documents.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        documents.append("\n".join(current))
    return documents


def _load_wikitext2_raw_urls(config: dict[str, Any], root: Path) -> CorpusLoadResult:
    split_urls = config.get("split_urls", {})
    if not isinstance(split_urls, dict) or not split_urls:
        raise ValueError("wikitext2_raw_urls provider requires split_urls")
    cache_dir = root / str(config.get("cache_dir", "data/real/wikitext2_raw"))
    split_documents: dict[str, list[str]] = {}
    local_paths: dict[str, str] = {}
    for split_name, url in split_urls.items():
        output_path = cache_dir / f"{split_name}.txt"
        _download_text(str(url), output_path)
        split_documents[str(split_name)] = _read_text_documents(output_path)
        try:
            local_paths[str(split_name)] = output_path.relative_to(root).as_posix()
        except ValueError:
            local_paths[str(split_name)] = output_path.name
    documents = [
        document
        for split_name in ["train", "dev", "valid", "validation", "test"]
        for document in split_documents.get(split_name, [])
    ]
    if not documents:
        raise RuntimeError("WikiText-2 raw URL loader produced zero documents")
    metadata = _metadata_from_config(config)
    metadata.update(
        {
            "provider": "wikitext2_raw_urls",
            "source": config.get("source"),
            "version": config.get("version", "wikitext-2-raw-v1"),
            "download_method": config.get("download_method", "urllib.request"),
            "license_or_terms": config.get("license_or_terms", config.get("license_note")),
            "local_path": local_paths,
            "dataset_status": "real_local_nonfallback",
            "dataset_scope": "official_split",
            "predefined_splits": {
                "train": split_documents.get("train", []),
                "dev": split_documents.get("dev")
                or split_documents.get("valid")
                or split_documents.get("validation", []),
                "test": split_documents.get("test", []),
            },
        }
    )
    return CorpusLoadResult(str(config["dataset_key"]), documents, metadata)


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
        "source": config.get("source") or config.get("hf_dataset") or config.get("path"),
        "version": config.get("version", ""),
        "download_method": config.get("download_method", ""),
        "local_path": config.get("path", ""),
        "license_note": config.get("license_note", "verify upstream license before use"),
        "license_or_terms": config.get(
            "license_or_terms",
            config.get("license_note", "verify upstream license before use"),
        ),
        "required_real_data": bool(config.get("required_real_data", False)),
        "is_smoke": bool(config.get("is_smoke", False)),
        "streaming": bool(config.get("streaming", False)),
        "seed": config.get("sample_seed", config.get("seed", 13)),
        "sample_seed": config.get("sample_seed", config.get("seed", 13)),
        "max_documents": config.get("max_documents", ""),
        "max_tokens": config.get("max_tokens", ""),
        "download_or_streaming_method": config.get(
            "download_or_streaming_method",
            config.get("download_method", ""),
        ),
        "is_streaming_sample": bool(config.get("is_streaming_sample", config.get("streaming", False))),
        "is_full_dataset": bool(config.get("is_full_dataset", False)),
        "used_fallback": False,
        "fallback_reason": "",
        "allow_fallback": bool(config.get("allow_fallback", False)),
        "dataset_status": (
            "smoke_fixture" if config.get("is_smoke") else "real_nonfallback"
        ),
        "dataset_scope": "smoke_fixture" if config.get("is_smoke") else "official_split",
    }


def _load_prepared_streaming_sample(config: dict[str, Any], root: Path) -> CorpusLoadResult:
    dataset_key = str(config["dataset_key"])
    output_dir = root / str(config.get("output_dir", f"artifacts/data/{dataset_key}"))
    manifest_path = output_dir / "data_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(
            f"Prepared streaming manifest missing for {dataset_key}; run "
            f"python scripts/prepare_streaming_data.py --config configs/data/{dataset_key}.yaml first."
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    dataset_status = str(manifest.get("dataset_status", "configured_not_run"))
    if dataset_status != "real_nonfallback":
        reason = manifest.get("failure_reason") or f"dataset_status={dataset_status}"
        raise RuntimeError(f"Prepared streaming sample is not usable: {reason}")
    split_dir = output_dir / "splits"
    splits = {
        "train": read_split_jsonl(split_dir / "train.jsonl"),
        "dev": read_split_jsonl(split_dir / "dev.jsonl"),
        "test": read_split_jsonl(split_dir / "test.jsonl"),
    }
    if not all(splits.values()):
        raise RuntimeError(f"Prepared streaming split files are incomplete for {dataset_key}")
    documents = [document for split_docs in splits.values() for document in split_docs]
    metadata = _metadata_from_config(config)
    metadata.update(
        {
            "provider": "prepared_streaming_sample",
            "source": manifest.get("source", config.get("hf_dataset", "")),
            "version": manifest.get("version", config.get("version", "")),
            "download_method": manifest.get("download_method", ""),
            "download_or_streaming_method": manifest.get(
                "download_or_streaming_method",
                "huggingface datasets streaming",
            ),
            "license_or_terms": manifest.get("license_or_terms", config.get("license_or_terms", "")),
            "local_path": {
                split: f"{output_dir.relative_to(root).as_posix()}/splits/{split}.jsonl"
                for split in splits
            },
            "dataset_status": dataset_status,
            "dataset_scope": str(manifest.get("dataset_scope", "streaming_sample")),
            "predefined_splits": splits,
            "is_streaming_sample": True,
            "is_full_dataset": False,
            "failure_reason": manifest.get("failure_reason", ""),
        }
    )
    return CorpusLoadResult(dataset_key, documents, metadata)


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
        elif provider in {"huggingface_streaming", "prepared_streaming_sample"}:
            return _load_prepared_streaming_sample(config, root)
        elif provider == "wikitext2_raw_urls":
            return _load_wikitext2_raw_urls(config, root)
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
