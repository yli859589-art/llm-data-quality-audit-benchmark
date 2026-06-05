from __future__ import annotations

import argparse
from pathlib import Path

from experiment_utils import root
from registry_utils import (
    append_run,
    config_hash,
    environment_hash,
    file_hash,
    make_run_id,
    now_utc,
    relative,
)

from data.dataset_manifest import write_dataset_manifest
from data.real_corpora import load_documents_from_config
from data.splitter import deterministic_split


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    command = f"python scripts/prepare_real_data.py --config {args.config}"
    config_path = root / args.config
    try:
        loaded = load_documents_from_config(config_path, root=root)
        seed = int(loaded.metadata.get("seed", 13))
        splits = loaded.metadata.get("predefined_splits") or deterministic_split(
            loaded.documents,
            seed=seed,
        )
        output_dir = (
            root / args.output_dir
            if args.output_dir
            else root / "artifacts" / "data" / loaded.dataset_key
        )
        metadata = dict(loaded.metadata)
        metadata.update(
            {
                "config_path": args.config,
                "generated_by_script": "scripts/prepare_real_data.py",
                "command": command,
            }
        )
        manifest = write_dataset_manifest(
            root=root,
            dataset_key=loaded.dataset_key,
            documents=loaded.documents,
            splits=splits,
            metadata=metadata,
            output_dir=output_dir,
        )
        latest_dir = root / "artifacts"
        write_dataset_manifest(
            root=root,
            dataset_key=loaded.dataset_key,
            documents=loaded.documents,
            splits=splits,
            metadata=metadata,
            output_dir=latest_dir,
        )
        manifest_path = output_dir / "data_manifest.json"
        timestamp = now_utc()
        snapshot_dir = output_dir / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        safe_timestamp = timestamp.replace(":", "").replace("+", "Z")
        snapshot_path = snapshot_dir / f"data_manifest_{safe_timestamp}.json"
        snapshot_path.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
        append_run(
            {
                "run_id": make_run_id("data", loaded.dataset_key, timestamp),
                "timestamp_utc": timestamp,
                "command": command,
                "config_path": args.config,
                "config_hash": config_hash(config_path),
                "dataset_key": loaded.dataset_key,
                "dataset_status": manifest["dataset_status"],
                "dataset_scope": manifest["dataset_scope"],
                "model_size": "none",
                "model_config_path": "",
                "model_config_hash": "",
                "baseline_name": "data_prepare",
                "seed": seed,
                "train_steps": 0,
                "train_tokens": manifest["actual_train_tokens"],
                "validation_tokens": manifest["actual_validation_tokens"],
                "run_status": "completed_filtering_only",
                "failure_reason": "",
                "artifact_path": relative(snapshot_path),
                "artifact_hash": file_hash(snapshot_path),
                "environment_fingerprint_hash": environment_hash(),
                "dataset_manifest_path": relative(manifest_path),
                "metrics_path": "",
                "retention_rate": "1.0",
            }
        )
        print(f"Prepared dataset: {loaded.dataset_key}")
        print(f"Documents: {manifest['document_count']}")
        print(f"Tokens: {manifest['token_count']}")
        print(f"Used fallback: {manifest['used_fallback']}")
        print(f"Dataset status: {manifest['dataset_status']}")
        print(f"Manifest: {manifest_path}")
    except Exception as exc:
        append_run(
            {
                "run_id": make_run_id("data", Path(args.config).stem, "failed", now_utc()),
                "timestamp_utc": now_utc(),
                "command": command,
                "config_path": args.config,
                "config_hash": config_hash(config_path),
                "dataset_key": Path(args.config).stem,
                "dataset_status": "failed_due_to_environment",
                "dataset_scope": "configured_not_run",
                "model_size": "none",
                "model_config_path": "",
                "model_config_hash": "",
                "baseline_name": "data_prepare",
                "seed": "",
                "train_steps": 0,
                "train_tokens": 0,
                "validation_tokens": 0,
                "run_status": "failed_due_to_environment",
                "failure_reason": f"{type(exc).__name__}: {exc}",
                "artifact_path": "",
                "artifact_hash": "",
                "environment_fingerprint_hash": environment_hash(),
                "dataset_manifest_path": "",
                "metrics_path": "",
                "retention_rate": "",
            }
        )
        print(f"Dataset preparation failed: {type(exc).__name__}: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
