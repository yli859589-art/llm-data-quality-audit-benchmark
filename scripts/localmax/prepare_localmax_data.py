from __future__ import annotations

import json
from pathlib import Path

from localmax_utils import (
    LOCALMAX_DATA,
    ROOT,
    count_tokens,
    gpt2_tokenizer,
    load_json,
    read_text_records,
    rel,
    sha256_file,
    source_dataset_specs,
    status_payload,
    write_json,
    write_report,
)


def _split_hash(paths: list[Path]) -> str:
    import hashlib

    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest().upper()


def main() -> None:
    blocking: list[str] = []
    dataset_rows = []
    tokenizer_loaded = False
    try:
        tokenizer = gpt2_tokenizer()
        tokenizer_loaded = True
    except Exception as exc:
        tokenizer = None
        blocking.append(f"GPT-2 tokenizer load failed, so LocalMax BPE token counts were not produced: {type(exc).__name__}: {exc}")

    for spec in source_dataset_specs():
        source_manifest = load_json(ROOT / spec["source_manifest_path"])
        split_paths = {name: ROOT / relative for name, relative in spec["split_paths"].items()}
        missing = [relative for relative in spec["split_paths"].values() if not (ROOT / relative).exists()]
        split_token_counts: dict[str, int] = {}
        split_record_counts: dict[str, int] = {}
        split_byte_counts: dict[str, int] = {}
        data_hash = ""
        total_tokens = 0
        if missing:
            blocking.append(f"{spec['dataset_id']} missing split files: {', '.join(missing)}")
        elif tokenizer_loaded and tokenizer is not None:
            data_hash = _split_hash(list(split_paths.values()))
            for split, path in split_paths.items():
                texts = read_text_records([path])
                split_record_counts[split] = len(texts)
                split_byte_counts[split] = path.stat().st_size
                split_token_counts[split] = count_tokens(tokenizer, texts)
            total_tokens = sum(split_token_counts.values())
        fallback_used = bool(source_manifest.get("used_fallback") or source_manifest.get("fallback_used"))
        if fallback_used:
            blocking.append(f"{spec['dataset_id']} source manifest reports fallback data.")
        meets_20m = total_tokens >= 20_000_000
        manifest = {
            "step": "step10B_localmax_execution",
            "stage": "data_manifest",
            "scope": "localmax_data",
            "dataset_id": spec["dataset_id"],
            "dataset_name": spec["dataset_name"],
            "source_manifest_path": spec["source_manifest_path"],
            "source_dataset_status": source_manifest.get("dataset_status", "unknown"),
            "fallback_used": fallback_used,
            "smoke_only": False,
            "streaming_sample": bool(spec["is_streaming_sample"]),
            "split_paths": spec["split_paths"],
            "split_gpt2_bpe_tokens": split_token_counts,
            "gpt2_bpe_tokens": total_tokens,
            "split_record_counts": split_record_counts,
            "split_byte_counts": split_byte_counts,
            "data_sha256": data_hash,
            "token_counter_type": "gpt2_bpe_transformers" if tokenizer_loaded else "unavailable",
            "minimum_localmax_dataset_tokens": 20_000_000,
            "recommended_token_budget_per_dataset": 50_000_000,
            "meets_localmax_20m_floor": meets_20m,
            "meets_recommended_50m_budget": total_tokens >= 50_000_000,
            "completed": not missing and tokenizer_loaded and not fallback_used,
            "localmax_completed": False,
            "level3_completed": False,
            "main_results_modified": False,
            "created_at": status_payload("data_manifest", True, [])["created_at"],
        }
        manifest_path = LOCALMAX_DATA / spec["dataset_id"] / "data_manifest.json"
        write_json(manifest_path, manifest)
        dataset_rows.append(
            {
                "dataset_id": spec["dataset_id"],
                "dataset_name": spec["dataset_name"],
                "manifest_path": rel(manifest_path),
                "gpt2_bpe_tokens": total_tokens,
                "fallback_used": fallback_used,
                "streaming_sample": bool(spec["is_streaming_sample"]),
                "meets_localmax_20m_floor": meets_20m,
                "meets_recommended_50m_budget": total_tokens >= 50_000_000,
                "source_manifest_path": spec["source_manifest_path"],
            }
        )

    datasets_meeting_floor = sum(1 for row in dataset_rows if row["meets_localmax_20m_floor"] and not row["fallback_used"])
    localmax_data_ready = datasets_meeting_floor >= 2
    if not localmax_data_ready:
        blocking.append(
            "LocalMax data gate requires at least two non-fallback datasets with >=20M GPT-2/BPE tokens; "
            f"current count is {datasets_meeting_floor}."
        )
    report = status_payload(
        "data",
        localmax_data_ready,
        sorted(set(blocking)),
        {
            "localmax_data_ready": localmax_data_ready,
            "partial_real_data_evidence": any(row["gpt2_bpe_tokens"] > 0 and not row["fallback_used"] for row in dataset_rows),
            "tokenizer_loaded_for_counts": tokenizer_loaded,
            "datasets": dataset_rows,
            "datasets_meeting_20m_floor": datasets_meeting_floor,
            "minimum_localmax_pass_line": "at_least_two_nonfallback_datasets_each_with_20m_or_more_gpt2_bpe_tokens",
            "notes": [
                "Existing WikiText-2, OpenWebText streaming, and C4 streaming data are real non-fallback evidence.",
                "They are below the LocalMax token floor and are therefore not promoted to completed LocalMax data.",
            ],
        },
    )
    write_json(LOCALMAX_DATA / "localmax_data_inventory.json", {"datasets": dataset_rows})
    write_report(report, "localmax_data_report", "LocalMax Data Report")
    print(json.dumps({"localmax_data_ready": localmax_data_ready, "datasets_meeting_20m_floor": datasets_meeting_floor}))


if __name__ == "__main__":
    main()

