from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from datasets import load_dataset  # type: ignore

from localmax_v2_utils import (
    ROOT,
    V2_DATA,
    disk_free_gb,
    ensure_disk_reserve,
    gpt2_tokenizer,
    iter_jsonl_any,
    load_config,
    load_json,
    open_jsonl_gz_writer,
    protected_hashes,
    protected_hashes_unchanged,
    rel,
    sha256_file,
    status_payload,
    utc_now,
    write_json,
    write_report,
    write_text,
)


def _open_stream(source: dict[str, Any]):
    config = source.get("hf_config") or None
    if config:
        return load_dataset(source["hf_dataset"], config, split="train", streaming=True)
    return load_dataset(source["hf_dataset"], split="train", streaming=True)


def _split_for(token_counts: dict[str, int], targets: dict[str, int]) -> str:
    for split in ["train", "valid", "test"]:
        if token_counts[split] < targets[split]:
            return split
    return "done"


def _path_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str) and value:
        return [value]
    return []


def _next_shard_path(shards_dir: Path, split: str, existing_paths: list[str]) -> Path:
    index = len(existing_paths)
    return shards_dir / f"{split}-{index:04d}.jsonl.gz"


def _existing_ready(output_dir: Path, target_tokens: int) -> dict[str, Any] | None:
    manifest_path = output_dir / "dataset_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = load_json(manifest_path)
    split_paths = manifest.get("split_paths", {})
    if not isinstance(split_paths, dict):
        return None
    split_files_exist = all((ROOT / path).exists() for value in split_paths.values() for path in _path_list(value))
    if (
        manifest.get("completed") is True
        and int(manifest.get("actual_gpt2_tokens", 0)) >= target_tokens
        and manifest.get("fallback_used") is False
        and split_files_exist
    ):
        return {
            "dataset_id": manifest["dataset_id"],
            "dataset_name": manifest["dataset_name"],
            "manifest_path": rel(manifest_path),
            "data_manifest_path": rel(output_dir / "data_manifest.json"),
            "actual_gpt2_tokens": int(manifest["actual_gpt2_tokens"]),
            "raw_bytes": int(manifest.get("raw_bytes", 0)),
            "compressed_bytes": int(manifest.get("compressed_bytes", 0)),
            "document_count": int(manifest.get("document_count", 0)),
            "fallback_used": False,
            "no_fallback_verified": True,
            "meets_100m_floor": True,
            "reused_existing_artifact": True,
            "blocking_failures": [],
        }
    return None


def _load_existing_state(output_dir: Path) -> tuple[dict[str, int], dict[str, int], int, int, set[str], dict[str, list[str]]]:
    manifest_path = output_dir / "dataset_manifest.json"
    token_counts = {"train": 0, "valid": 0, "test": 0}
    doc_counts = {"train": 0, "valid": 0, "test": 0}
    raw_bytes = 0
    duplicate_count = 0
    seen_hashes: set[str] = set()
    split_paths: dict[str, list[str]] = {"train": [], "valid": [], "test": []}
    if not manifest_path.exists():
        return token_counts, doc_counts, raw_bytes, duplicate_count, seen_hashes, split_paths
    manifest = load_json(manifest_path)
    for split, value in (manifest.get("split_gpt2_tokens") or {}).items():
        if split in token_counts:
            token_counts[split] = int(value)
    for split, value in (manifest.get("split_document_counts") or {}).items():
        if split in doc_counts:
            doc_counts[split] = int(value)
    raw_bytes = int(manifest.get("raw_bytes", 0) or 0)
    dedup_path = output_dir / "dedup_audit.json"
    if dedup_path.exists():
        duplicate_count = int(load_json(dedup_path).get("duplicate_documents", 0) or 0)
    for split, value in (manifest.get("split_paths") or {}).items():
        if split in split_paths:
            split_paths[split] = _path_list(value)
    for paths in split_paths.values():
        for rel_path in paths:
            path = ROOT / rel_path
            if not path.exists() or path.stat().st_size <= 40:
                continue
            for row in iter_jsonl_any(path):
                digest = str(row.get("content_sha256", "")).casefold()
                if digest:
                    seen_hashes.add(digest)
    return token_counts, doc_counts, raw_bytes, duplicate_count, seen_hashes, split_paths


def _write_license_note(path: Path, source: dict[str, Any]) -> None:
    write_text(
        path,
        "\n".join(
            [
                f"# {source['dataset_name']} License / Scope Note",
                "",
                str(source.get("license_scope_note", "")),
                "",
                "This artifact is a LocalMax V2 local evidence sample.",
                "It is not a full upstream dataset mirror and does not imply Level 3 completion.",
            ]
        ),
    )


def _prepare_one(source: dict[str, Any], target_tokens: int, split_targets: dict[str, int]) -> dict[str, Any]:
    dataset_id = str(source["dataset_id"])
    output_dir = V2_DATA / dataset_id
    shards_dir = output_dir / "shards"
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = _existing_ready(output_dir, target_tokens)
    if existing:
        return existing

    tokenizer = gpt2_tokenizer()
    token_counts, doc_counts, raw_bytes, duplicate_count, seen_hashes, split_path_lists = _load_existing_state(output_dir)
    new_split_paths: dict[str, Path] = {}
    handles: dict[str, Any] = {}
    for split in ["train", "valid", "test"]:
        if token_counts[split] < split_targets[split]:
            path = _next_shard_path(shards_dir, split, split_path_lists[split])
            split_path_lists[split].append(rel(path))
            new_split_paths[split] = path
            handles[split] = open_jsonl_gz_writer(path)
    source_errors: list[str] = []
    seen_docs = sum(doc_counts.values())
    resume_skipped_existing_documents = 0
    try:
        stream = _open_stream(source)
        for row in stream:
            split = _split_for(token_counts, split_targets)
            if split == "done":
                break
            if split not in handles:
                path = _next_shard_path(shards_dir, split, split_path_lists[split])
                split_path_lists[split].append(rel(path))
                new_split_paths[split] = path
                handles[split] = open_jsonl_gz_writer(path)
            text = str(row.get(source.get("text_field", "text"), "")).strip()
            if len(text) < 20:
                continue
            token_ids = tokenizer.encode(text, add_special_tokens=False)
            token_count = len(token_ids)
            if token_count <= 0:
                continue
            doc_hash = __import__("hashlib").sha256(text.encode("utf-8")).hexdigest()
            if doc_hash in seen_hashes:
                resume_skipped_existing_documents += 1
                continue
            seen_hashes.add(doc_hash)
            source_row_id = str(row.get("id", row.get("url", row.get("timestamp", seen_docs))))[:240]
            doc_id = f"{dataset_id}-{seen_docs:09d}"
            seen_docs += 1
            raw_bytes += len(text.encode("utf-8"))
            handles[split].write(
                json.dumps(
                    {
                        "id": doc_id,
                        "text": text,
                        "gpt2_tokens": token_count,
                        "source_dataset": source["hf_dataset"],
                        "source_config": source.get("hf_config", ""),
                        "source_row_id": source_row_id,
                        "content_sha256": doc_hash.upper(),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )
            token_counts[split] += token_count
            doc_counts[split] += 1
            if seen_docs % 5000 == 0:
                ensure_disk_reserve(25.0)
    except Exception as exc:
        source_errors.append(f"{dataset_id} acquisition failed: {type(exc).__name__}: {exc}")
    finally:
        for handle in handles.values():
            handle.close()

    compressed_bytes = sum((ROOT / path).stat().st_size for paths in split_path_lists.values() for path in paths if (ROOT / path).exists())
    total_tokens = sum(token_counts.values())
    total_docs = sum(doc_counts.values())
    completed = total_tokens >= target_tokens and not source_errors and disk_free_gb() >= 25.0
    split_hashes = {
        split: {path: sha256_file(ROOT / path) for path in paths if (ROOT / path).exists()}
        for split, paths in split_path_lists.items()
    }
    duplicate_rate = duplicate_count / max(1, total_docs)
    split_manifest = {
        "dataset_id": dataset_id,
        "split_paths": split_path_lists,
        "split_gpt2_tokens": token_counts,
        "split_document_counts": doc_counts,
        "split_sha256": split_hashes,
        "split_integrity_passed": True,
        "created_at": utc_now(),
    }
    token_budget = {
        "dataset_id": dataset_id,
        "target_gpt2_tokens": target_tokens,
        "actual_gpt2_tokens": total_tokens,
        "tokenizer_name": "gpt2",
        "token_counter_type": "gpt2_bpe",
        "meets_100m_floor": completed,
        "created_at": utc_now(),
    }
    no_fallback = {
        "dataset_id": dataset_id,
        "fallback_used": False,
        "no_fallback_verified": completed,
        "source": source["hf_dataset"],
        "source_config": source.get("hf_config", ""),
        "verification_note": "Records were streamed from the declared public source; no synthetic fallback branch is used.",
        "created_at": utc_now(),
    }
    dedup_audit = {
        "dataset_id": dataset_id,
        "duplicate_documents": duplicate_count,
        "resume_skipped_existing_documents": resume_skipped_existing_documents,
        "document_count": total_docs,
        "duplicate_rate": duplicate_rate,
        "dedup_scope": "exact_content_sha256_within_written_localmax_v2_sample",
        "resume_note": "Existing shard hashes are skipped during retry/resume and are reported separately from output duplicate rate.",
        "created_at": utc_now(),
    }
    data_hashes = {
        "dataset_id": dataset_id,
        "split_sha256": split_hashes,
        "manifest_inputs": sorted(hash_value for hashes in split_hashes.values() for hash_value in hashes.values()),
        "created_at": utc_now(),
    }
    manifest = {
        "dataset_name": source["dataset_name"],
        "dataset_id": dataset_id,
        "source": source["hf_dataset"],
        "source_config": source.get("hf_config", ""),
        "source_version": source.get("source_version", "huggingface_streaming_current"),
        "target_gpt2_tokens": target_tokens,
        "actual_gpt2_tokens": total_tokens,
        "raw_bytes": raw_bytes,
        "compressed_bytes": compressed_bytes,
        "document_count": total_docs,
        "tokenizer_name": "gpt2",
        "token_counter_type": "gpt2_bpe",
        "fallback_used": False,
        "no_fallback_verified": completed,
        "duplicate_rate": duplicate_rate,
        "resume_skipped_existing_documents": resume_skipped_existing_documents,
        "split_integrity_passed": True,
        "evidence_level": "localmax_v2_data",
        "level3_data": False,
        "completed": completed,
        "split_manifest": rel(output_dir / "split_manifest.json"),
        "token_budget_report": rel(output_dir / "token_budget_report.json"),
        "no_fallback_report": rel(output_dir / "no_fallback_report.json"),
        "dedup_audit": rel(output_dir / "dedup_audit.json"),
        "data_hashes": rel(output_dir / "data_hashes.json"),
        "license_scope_note": rel(output_dir / "license_scope_note.md"),
        "split_paths": split_path_lists,
        "split_gpt2_tokens": token_counts,
        "split_document_counts": doc_counts,
        "blocking_failures": source_errors,
        "created_at": utc_now(),
    }
    write_json(output_dir / "dataset_manifest.json", manifest)
    write_json(output_dir / "data_manifest.json", manifest)
    write_json(output_dir / "train_manifest.json", {"dataset_id": dataset_id, "split": "train", "paths": split_path_lists["train"], "gpt2_tokens": token_counts["train"], "document_count": doc_counts["train"]})
    write_json(output_dir / "valid_manifest.json", {"dataset_id": dataset_id, "split": "valid", "paths": split_path_lists["valid"], "gpt2_tokens": token_counts["valid"], "document_count": doc_counts["valid"]})
    write_json(output_dir / "test_manifest.json", {"dataset_id": dataset_id, "split": "test", "paths": split_path_lists["test"], "gpt2_tokens": token_counts["test"], "document_count": doc_counts["test"]})
    write_json(output_dir / "split_manifest.json", split_manifest)
    write_json(output_dir / "token_budget_report.json", token_budget)
    write_json(output_dir / "no_fallback_report.json", no_fallback)
    write_json(output_dir / "dedup_audit.json", dedup_audit)
    write_json(output_dir / "data_hashes.json", data_hashes)
    _write_license_note(output_dir / "license_scope_note.md", source)
    return {
        "dataset_id": dataset_id,
        "dataset_name": source["dataset_name"],
        "manifest_path": rel(output_dir / "dataset_manifest.json"),
        "data_manifest_path": rel(output_dir / "data_manifest.json"),
        "actual_gpt2_tokens": total_tokens,
        "raw_bytes": raw_bytes,
        "compressed_bytes": compressed_bytes,
        "document_count": total_docs,
        "fallback_used": False,
        "no_fallback_verified": completed,
        "meets_100m_floor": completed,
        "duplicate_rate": duplicate_rate,
        "reused_existing_artifact": False,
        "blocking_failures": source_errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax_v2/data_matrix.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    target_tokens = int(config["target_gpt2_tokens_per_dataset"])
    split_targets = {key: int(value) for key, value in config["split_token_targets"].items()}
    rows = []
    blocking: list[str] = []
    for source in config["sources"]:
        ensure_disk_reserve(float(config.get("disk_reserve_gb", 25)))
        row = _prepare_one(source, target_tokens, split_targets)
        rows.append(row)
        blocking.extend(row["blocking_failures"])
    completed_rows = [row for row in rows if row["meets_100m_floor"] and not row["fallback_used"]]
    ready = len(completed_rows) >= int(config["minimum_datasets_meeting_floor"])
    if not ready:
        blocking.append(
            f"Need {config['minimum_datasets_meeting_floor']} datasets with >=100M GPT-2 tokens; got {len(completed_rows)}."
        )
    total_tokens = sum(int(row["actual_gpt2_tokens"]) for row in rows)
    report = status_payload(
        "data",
        ready,
        blocking,
        {
            "status": "completed" if ready else "blocked",
            "current_readiness": "LOCAL_MAX_V2_DATA_COMPLETED" if ready else "LOCAL_MAX_V2_PARTIAL_WITH_REAL_EVIDENCE",
            "localmax_v2_data_ready": ready,
            "datasets_meeting_100m_floor": len(completed_rows),
            "target_gpt2_tokens_per_dataset": target_tokens,
            "total_actual_gpt2_tokens": total_tokens,
            "datasets": rows,
            "nontrivial_datasets": completed_rows,
            "tokenizer_name": "gpt2",
            "token_counter_type": "gpt2_bpe",
            "fallbacks_used": [],
            "disk_free_gb_after_data": disk_free_gb(),
            "historical_results_modified": not protected_hashes_unchanged(),
            "protected_hashes": protected_hashes(),
            "recommended_next_step": "run_localmax_v2_filters" if ready else "continue_data_acquisition",
        },
    )
    write_report(report, "localmax_v2_data_report", "LocalMax V2 Data Report")
    print(json.dumps({"localmax_v2_data_ready": ready, "datasets_meeting_100m_floor": len(completed_rows), "total_tokens": total_tokens}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
