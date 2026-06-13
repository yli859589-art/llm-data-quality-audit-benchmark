from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from datasets import load_dataset  # type: ignore

from localmax_utils import (
    LOCALMAX_DATA,
    ROOT,
    gpt2_tokenizer,
    protected_hashes,
    protected_hashes_unchanged,
    rel,
    sha256_file,
    status_payload,
    utc_now,
    write_json,
    write_report,
)


def _load_config(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _open_stream(source: dict[str, Any]):
    name = source["hf_dataset"]
    config = source.get("hf_config") or None
    if config:
        return load_dataset(name, config, split="train", streaming=True)
    return load_dataset(name, split="train", streaming=True)


def _split_for(counts: dict[str, int], targets: dict[str, int]) -> str:
    for split in ["train", "valid", "test"]:
        if counts[split] < targets[split]:
            return split
    return "done"


def _write_license_note(path: Path, source: dict[str, Any]) -> None:
    path.write_text(
        "\n".join(
            [
                f"# {source['dataset_name']} License / Scope Note",
                "",
                str(source.get("license_scope_note", "")),
                "",
                "This artifact is bounded LocalMax minimal evidence.",
                "It is not Level 3 data and does not support Level 3 completion claims.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _prepare_one(source: dict[str, Any], target_tokens: int, split_targets: dict[str, int]) -> dict[str, Any]:
    dataset_id = str(source["dataset_id"])
    output_dir = LOCALMAX_DATA / dataset_id
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_manifest_path = output_dir / "dataset_manifest.json"
    if existing_manifest_path.exists():
        existing = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
        split_paths = existing.get("split_paths", {})
        split_files_exist = all((ROOT / path).exists() for path in split_paths.values())
        if existing.get("completed") is True and int(existing.get("actual_gpt2_tokens", 0)) >= target_tokens and split_files_exist:
            return {
                "dataset_id": dataset_id,
                "dataset_name": source["dataset_name"],
                "manifest_path": rel(existing_manifest_path),
                "data_manifest_path": rel(output_dir / "data_manifest.json"),
                "actual_gpt2_tokens": int(existing["actual_gpt2_tokens"]),
                "document_count": sum(int(value) for value in existing.get("split_document_counts", {}).values()),
                "fallback_used": False,
                "no_fallback_verified": True,
                "meets_20m_floor": True,
                "source": source["hf_dataset"],
                "source_config": source.get("hf_config", ""),
                "blocking_failures": [],
                "reused_existing_artifact": True,
            }
    tokenizer = gpt2_tokenizer()
    tokenizer.model_max_length = 10**12
    split_paths = {
        "train": output_dir / "train.jsonl",
        "valid": output_dir / "valid.jsonl",
        "test": output_dir / "test.jsonl",
    }
    handles = {split: path.open("w", encoding="utf-8") for split, path in split_paths.items()}
    token_counts = {"train": 0, "valid": 0, "test": 0}
    doc_counts = {"train": 0, "valid": 0, "test": 0}
    failures: list[str] = []
    seen_docs = 0
    try:
        stream = _open_stream(source)
        for row in stream:
            split = _split_for(token_counts, split_targets)
            if split == "done":
                break
            text = str(row.get(source.get("text_field", "text"), "")).strip()
            if len(text) < 20:
                continue
            token_ids = tokenizer.encode(text, add_special_tokens=False)
            token_count = len(token_ids)
            if token_count <= 0:
                continue
            doc_id = f"{dataset_id}-{seen_docs}"
            seen_docs += 1
            record = {
                "id": doc_id,
                "text": text,
                "gpt2_tokens": token_count,
                "source_dataset": source["hf_dataset"],
                "source_config": source.get("hf_config", ""),
                "source_row_id": str(row.get("id", row.get("url", doc_id)))[:200],
            }
            handles[split].write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            token_counts[split] += token_count
            doc_counts[split] += 1
    except Exception as exc:
        failures.append(f"{dataset_id} acquisition failed: {type(exc).__name__}: {exc}")
    finally:
        for handle in handles.values():
            handle.close()
    total_tokens = sum(token_counts.values())
    completed = total_tokens >= target_tokens and not failures
    split_hashes = {
        split: sha256_file(path) if path.exists() else ""
        for split, path in split_paths.items()
    }
    split_manifest = {
        "dataset_id": dataset_id,
        "split_paths": {split: rel(path) for split, path in split_paths.items()},
        "split_gpt2_tokens": token_counts,
        "split_document_counts": doc_counts,
        "split_sha256": split_hashes,
        "created_at": utc_now(),
    }
    data_hashes = {
        "dataset_id": dataset_id,
        "combined_split_hashes": split_hashes,
        "manifest_hash_inputs": sorted(split_hashes.values()),
        "created_at": utc_now(),
    }
    no_fallback = {
        "dataset_id": dataset_id,
        "fallback_used": False,
        "no_fallback_verified": completed,
        "source": source["hf_dataset"],
        "verification_note": "Data records were streamed from the declared public source; no synthetic fallback branch is used.",
        "created_at": utc_now(),
    }
    token_budget = {
        "dataset_id": dataset_id,
        "target_gpt2_tokens": target_tokens,
        "actual_gpt2_tokens": total_tokens,
        "meets_20m_floor": completed,
        "tokenizer_name": "gpt2",
        "token_counter_type": "gpt2_bpe",
        "created_at": utc_now(),
    }
    manifest = {
        "dataset_name": source["dataset_name"],
        "dataset_id": dataset_id,
        "source": source["hf_dataset"],
        "source_config": source.get("hf_config", ""),
        "source_version": source.get("source_version", "huggingface_current"),
        "target_gpt2_tokens": target_tokens,
        "actual_gpt2_tokens": total_tokens,
        "tokenizer_name": "gpt2",
        "token_counter_type": "gpt2_bpe",
        "fallback_used": False,
        "no_fallback_verified": completed,
        "evidence_level": "localmax_data_minimal",
        "level3_data": False,
        "smoke_only": False,
        "protocol_only": False,
        "completed": completed,
        "split_manifest_path": rel(output_dir / "split_manifest.json"),
        "token_budget_report_path": rel(output_dir / "token_budget_report.json"),
        "no_fallback_report_path": rel(output_dir / "no_fallback_report.json"),
        "data_hashes_path": rel(output_dir / "data_hashes.json"),
        "license_scope_note_path": rel(output_dir / "license_scope_note.md"),
        "split_paths": {split: rel(path) for split, path in split_paths.items()},
        "split_gpt2_tokens": token_counts,
        "split_document_counts": doc_counts,
        "blocking_failures": failures,
        "created_at": utc_now(),
    }
    write_json(output_dir / "dataset_manifest.json", manifest)
    write_json(output_dir / "data_manifest.json", manifest)
    write_json(output_dir / "split_manifest.json", split_manifest)
    write_json(output_dir / "token_budget_report.json", token_budget)
    write_json(output_dir / "no_fallback_report.json", no_fallback)
    write_json(output_dir / "data_hashes.json", data_hashes)
    _write_license_note(output_dir / "license_scope_note.md", source)
    return {
        "dataset_id": dataset_id,
        "dataset_name": source["dataset_name"],
        "manifest_path": rel(output_dir / "dataset_manifest.json"),
        "data_manifest_path": rel(output_dir / "data_manifest.json"),
        "actual_gpt2_tokens": total_tokens,
        "document_count": sum(doc_counts.values()),
        "fallback_used": False,
        "no_fallback_verified": completed,
        "meets_20m_floor": completed,
        "source": source["hf_dataset"],
        "source_config": source.get("hf_config", ""),
        "blocking_failures": failures,
        "reused_existing_artifact": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax/data_matrix_minimal.yaml")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = _load_config(args.config)
    random.seed(13)
    rows = []
    blocking: list[str] = []
    target_tokens = int(config["target_gpt2_tokens"])
    split_targets = {key: int(value) for key, value in config["split_token_targets"].items()}
    for source in config["sources"]:
        if len([row for row in rows if row["meets_20m_floor"]]) >= int(config["minimum_datasets_meeting_floor"]):
            break
        row = _prepare_one(source, target_tokens, split_targets)
        rows.append(row)
        blocking.extend(row["blocking_failures"])
    nontrivial = [row for row in rows if row["meets_20m_floor"] and not row["fallback_used"]]
    ready = len(nontrivial) >= int(config["minimum_datasets_meeting_floor"])
    if not ready:
        blocking.append(
            f"Need {config['minimum_datasets_meeting_floor']} datasets with >=20M GPT-2/BPE tokens; got {len(nontrivial)}."
        )
    report = status_payload(
        "data",
        ready,
        sorted(set(blocking)),
        {
            "status": "completed" if ready else "blocked",
            "step": "step10B_localmax_execution_fix",
            "localmax_data_ready": ready,
            "datasets_meeting_20m_floor": len(nontrivial),
            "nontrivial_datasets": nontrivial,
            "datasets": rows,
            "target_gpt2_tokens": target_tokens,
            "tokenizer_name": "gpt2",
            "token_counter_type": "gpt2_bpe",
            "fallbacks_used": [],
            "recommended_next_step": "run_localmax_minimal_filters" if ready else "continue_data_acquisition",
            "level3_data_ready": False,
            "level3_completed_artifact": False,
            "main_results_modified": False,
            "historical_results_modified": not protected_hashes_unchanged(),
            "protected_hashes": protected_hashes(),
        },
    )
    write_report(report, "localmax_data_report", "LocalMax Minimal Data Report")
    print(json.dumps({"localmax_data_ready": ready, "datasets_meeting_20m_floor": len(nontrivial)}))


if __name__ == "__main__":
    main()
