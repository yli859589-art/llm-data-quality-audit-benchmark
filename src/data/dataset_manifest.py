from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

from .splitter import stable_document_id
from .token_counting import count_tokens


def _project_relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _corpus_sha256(documents: list[str]) -> str:
    digest = hashlib.sha256()
    for document in documents:
        digest.update(document.encode("utf-8"))
        digest.update(b"\n<doc-boundary>\n")
    return digest.hexdigest()


def write_dataset_manifest(
    *,
    root: Path,
    dataset_key: str,
    documents: list[str],
    splits: dict[str, list[str]],
    metadata: dict[str, Any],
    output_dir: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    split_rows = []
    split_lookup = {"train": {}, "dev": {}, "test": {}}
    split_document_hashes: dict[str, list[str]] = {}
    for split_name, split_docs in splits.items():
        row = {
            "split": split_name,
            "documents": len(split_docs),
            "tokens": sum(count_tokens(document) for document in split_docs),
            "bytes": sum(len(document.encode("utf-8")) for document in split_docs),
            "sha256": _corpus_sha256(split_docs),
        }
        split_rows.append(row)
        split_document_hashes[split_name] = [
            stable_document_id(document) for document in split_docs
        ]
        if split_name in split_lookup:
            split_lookup[split_name] = row

    manifest = {
        "dataset": metadata.get("dataset_name", dataset_key),
        "dataset_key": dataset_key,
        "dataset_name": metadata.get("dataset_name", dataset_key),
        "config_path": metadata.get("config_path", ""),
        "provider": metadata.get("provider"),
        "source": metadata.get("source"),
        "version": metadata.get("version", ""),
        "download_method": metadata.get("download_method", ""),
        "download_or_streaming_method": metadata.get(
            "download_or_streaming_method",
            metadata.get("download_method", ""),
        ),
        "local_path": metadata.get("local_path", ""),
        "split": metadata.get("split", "train/dev/test"),
        "dataset_status": metadata.get("dataset_status", ""),
        "dataset_scope": metadata.get("dataset_scope", ""),
        "sample_seed": metadata.get("seed"),
        "max_documents": metadata.get("max_documents", ""),
        "max_tokens": metadata.get("max_tokens", ""),
        "license_note": metadata.get("license_note", "verify upstream license before release"),
        "license_or_terms": metadata.get(
            "license_or_terms",
            metadata.get("license_note", "verify upstream license before release"),
        ),
        "allow_fallback": bool(metadata.get("allow_fallback", False)),
        "required_real_data": bool(metadata.get("required_real_data", False)),
        "is_smoke": bool(metadata.get("is_smoke", False)),
        "used_fallback": bool(metadata.get("used_fallback", False)),
        "fallback_reason": metadata.get("fallback_reason", ""),
        "failure_reason": metadata.get("failure_reason", ""),
        "generated_by_script": metadata.get("generated_by_script", ""),
        "command": metadata.get("command", ""),
        "streaming": bool(metadata.get("streaming", False)),
        "is_streaming_sample": bool(
            metadata.get("is_streaming_sample", metadata.get("streaming", False))
        ),
        "is_full_dataset": bool(metadata.get("is_full_dataset", False)),
        "seed": metadata.get("seed"),
        "document_count": len(documents),
        "actual_documents": len(documents),
        "token_count": sum(count_tokens(document) for document in documents),
        "actual_train_tokens": split_lookup["train"].get("tokens", 0),
        "actual_validation_tokens": split_lookup["dev"].get("tokens", 0),
        "actual_test_tokens": split_lookup["test"].get("tokens", 0),
        "byte_count": sum(len(document.encode("utf-8")) for document in documents),
        "corpus_sha256": _corpus_sha256(documents),
        "sha256_or_content_hash": _corpus_sha256(documents),
        "content_hash": _corpus_sha256(documents),
        "split_hash_train": split_lookup["train"].get("sha256", ""),
        "split_hash_dev": split_lookup["dev"].get("sha256", ""),
        "split_hash_test": split_lookup["test"].get("sha256", ""),
        "split_document_hashes": split_document_hashes,
        "split_summary": split_rows,
        "document_hashes": [
            {
                "index": index,
                "sha256": stable_document_id(document),
                "tokens": count_tokens(document),
                "bytes": len(document.encode("utf-8")),
            }
            for index, document in enumerate(documents)
        ],
    }

    json_path = output_dir / "data_manifest.json"
    csv_path = output_dir / "data_manifest.csv"
    md_path = output_dir / "data_manifest.md"
    json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "dataset",
                "config_path",
                "split",
                "dataset_status",
                "dataset_scope",
                "documents",
                "tokens",
                "bytes",
                "sha256",
                "allow_fallback",
                "required_real_data",
                "failure_reason",
                "sample_seed",
                "max_documents",
                "max_tokens",
                "actual_documents",
                "actual_train_tokens",
                "actual_validation_tokens",
                "actual_test_tokens",
                "content_hash",
                "is_streaming_sample",
                "is_full_dataset",
            ],
        )
        writer.writeheader()
        writer.writerows(
            {
                "dataset": manifest["dataset"],
                "config_path": manifest["config_path"],
                "split": row["split"],
                "dataset_status": manifest["dataset_status"],
                "dataset_scope": manifest["dataset_scope"],
                "documents": row["documents"],
                "tokens": row["tokens"],
                "bytes": row["bytes"],
                "sha256": row["sha256"],
                "allow_fallback": manifest["allow_fallback"],
                "required_real_data": manifest["required_real_data"],
                "failure_reason": manifest["failure_reason"],
                "sample_seed": manifest["sample_seed"],
                "max_documents": manifest["max_documents"],
                "max_tokens": manifest["max_tokens"],
                "actual_documents": manifest["actual_documents"],
                "actual_train_tokens": manifest["actual_train_tokens"],
                "actual_validation_tokens": manifest["actual_validation_tokens"],
                "actual_test_tokens": manifest["actual_test_tokens"],
                "content_hash": manifest["content_hash"],
                "is_streaming_sample": manifest["is_streaming_sample"],
                "is_full_dataset": manifest["is_full_dataset"],
            }
            for row in split_rows
        )

    md_lines = [
        f"# Dataset Manifest: {dataset_key}",
        "",
        f"- Provider: `{manifest['provider']}`",
        f"- Source: `{manifest['source']}`",
        f"- Dataset status: `{manifest['dataset_status']}`",
        f"- Dataset scope: `{manifest['dataset_scope']}`",
        f"- Streaming sample: `{manifest['is_streaming_sample']}`",
        f"- Complete upstream corpus: `{manifest['is_full_dataset']}`",
        f"- Max documents: `{manifest['max_documents']}`",
        f"- Max tokens: `{manifest['max_tokens']}`",
        f"- Required real data: `{manifest['required_real_data']}`",
        f"- Allow fallback: `{manifest['allow_fallback']}`",
        f"- Smoke mode: `{manifest['is_smoke']}`",
        f"- Used fallback: `{manifest['used_fallback']}`",
        f"- Corpus SHA-256: `{manifest['corpus_sha256']}`",
        "",
        "| Split | Documents | Tokens | Bytes | SHA-256 |",
        "|---|---:|---:|---:|---|",
    ]
    for row in split_rows:
        md_lines.append(
            f"| {row['split']} | {row['documents']} | {row['tokens']} | "
            f"{row['bytes']} | `{row['sha256']}` |"
        )
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    manifest["artifact_paths"] = {
        "json": _project_relative(json_path, root),
        "csv": _project_relative(csv_path, root),
        "markdown": _project_relative(md_path, root),
    }
    json_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest
