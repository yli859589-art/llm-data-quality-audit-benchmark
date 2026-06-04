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
    for split_name, split_docs in splits.items():
        split_rows.append(
            {
                "split": split_name,
                "documents": len(split_docs),
                "tokens": sum(count_tokens(document) for document in split_docs),
                "bytes": sum(len(document.encode("utf-8")) for document in split_docs),
                "sha256": _corpus_sha256(split_docs),
            }
        )

    manifest = {
        "dataset_key": dataset_key,
        "dataset_name": metadata.get("dataset_name", dataset_key),
        "provider": metadata.get("provider"),
        "source": metadata.get("source"),
        "license_note": metadata.get("license_note", "verify upstream license before release"),
        "required_real_data": bool(metadata.get("required_real_data", False)),
        "is_smoke": bool(metadata.get("is_smoke", False)),
        "used_fallback": bool(metadata.get("used_fallback", False)),
        "fallback_reason": metadata.get("fallback_reason", ""),
        "streaming": bool(metadata.get("streaming", False)),
        "seed": metadata.get("seed"),
        "document_count": len(documents),
        "token_count": sum(count_tokens(document) for document in documents),
        "byte_count": sum(len(document.encode("utf-8")) for document in documents),
        "corpus_sha256": _corpus_sha256(documents),
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
            fieldnames=["split", "documents", "tokens", "bytes", "sha256"],
        )
        writer.writeheader()
        writer.writerows(split_rows)

    md_lines = [
        f"# Dataset Manifest: {dataset_key}",
        "",
        f"- Provider: `{manifest['provider']}`",
        f"- Source: `{manifest['source']}`",
        f"- Required real data: `{manifest['required_real_data']}`",
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
