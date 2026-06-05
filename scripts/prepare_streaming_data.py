from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
from pathlib import Path

from data.dataset_cards import write_dataset_card
from data.dataset_manifest import write_dataset_manifest
from data.splitter import deterministic_split
from data.streaming_loader import (
    StreamingDataError,
    load_huggingface_streaming_sample,
    write_split_jsonl,
)
from experiment_utils import load_json_yaml, root
from registry_utils import (
    append_run,
    config_hash,
    environment_hash,
    file_hash,
    make_run_id,
    now_utc,
    relative,
)


def _command(config_path: str, force: bool) -> str:
    command = f"python scripts/prepare_streaming_data.py --config {config_path}"
    if force:
        command += " --force"
    return command


def _empty_splits() -> dict[str, list[str]]:
    return {"train": [], "dev": [], "test": []}


def _status_from_thresholds(manifest: dict[str, object], config: dict[str, object]) -> tuple[str, str]:
    min_documents = int(config.get("min_documents", 1) or 1)
    min_train_tokens = int(config.get("min_train_tokens", 1) or 1)
    min_validation_tokens = int(config.get("min_validation_tokens", 1) or 1)
    min_test_tokens = int(config.get("min_test_tokens", 1) or 1)
    actual_documents = int(manifest.get("actual_documents") or 0)
    actual_train = int(manifest.get("actual_train_tokens") or 0)
    actual_validation = int(manifest.get("actual_validation_tokens") or 0)
    actual_test = int(manifest.get("actual_test_tokens") or 0)
    failures = []
    if actual_documents < min_documents:
        failures.append(f"actual_documents {actual_documents} < min_documents {min_documents}")
    if actual_train < min_train_tokens:
        failures.append(f"actual_train_tokens {actual_train} < min_train_tokens {min_train_tokens}")
    if actual_validation < min_validation_tokens:
        failures.append(
            f"actual_validation_tokens {actual_validation} < min_validation_tokens {min_validation_tokens}"
        )
    if actual_test < min_test_tokens:
        failures.append(f"actual_test_tokens {actual_test} < min_test_tokens {min_test_tokens}")
    if failures:
        return "insufficient_streaming_sample", "; ".join(failures)
    return "real_nonfallback", ""


def _write_manifest(
    *,
    config: dict[str, object],
    config_path: str,
    command: str,
    documents: list[str],
    splits: dict[str, list[str]],
    output_dir: Path,
    dataset_status: str,
    failure_reason: str,
) -> dict[str, object]:
    dataset_key = str(config["dataset_key"])
    metadata = {
        "dataset_name": config.get("dataset_name", dataset_key),
        "provider": "huggingface_streaming",
        "source": config.get("hf_dataset", config.get("source", "")),
        "version": config.get("version", ""),
        "download_method": "huggingface datasets streaming",
        "download_or_streaming_method": "huggingface datasets streaming",
        "local_path": {
            split: f"{output_dir.relative_to(root).as_posix()}/splits/{split}.jsonl"
            for split in ["train", "dev", "test"]
        },
        "license_note": config.get("license_note", "verify upstream terms before release"),
        "license_or_terms": config.get(
            "license_or_terms",
            config.get("license_note", "verify upstream terms before release"),
        ),
        "required_real_data": True,
        "allow_fallback": False,
        "is_smoke": False,
        "streaming": True,
        "is_streaming_sample": True,
        "is_full_dataset": False,
        "seed": config.get("sample_seed", config.get("seed", 13)),
        "sample_seed": config.get("sample_seed", config.get("seed", 13)),
        "max_documents": config.get("max_documents", ""),
        "max_tokens": config.get("max_tokens", ""),
        "used_fallback": False,
        "fallback_reason": "",
        "failure_reason": failure_reason,
        "dataset_status": dataset_status,
        "dataset_scope": "streaming_sample",
        "config_path": config_path,
        "generated_by_script": "scripts/prepare_streaming_data.py",
        "command": command,
    }
    manifest = write_dataset_manifest(
        root=root,
        dataset_key=dataset_key,
        documents=documents,
        splits=splits,
        metadata=metadata,
        output_dir=output_dir,
    )
    write_dataset_card(manifest, output_dir)
    return manifest


def _append_prepare_run(
    *,
    config: dict[str, object],
    config_path: str,
    command: str,
    manifest_path: Path,
    manifest: dict[str, object],
) -> None:
    dataset_status = str(manifest.get("dataset_status", "failed_due_to_environment"))
    run_status = "completed_filtering_only" if dataset_status == "real_nonfallback" else dataset_status
    if run_status == "insufficient_streaming_sample":
        run_status = "failed_due_to_environment"
    append_run(
        {
            "run_id": make_run_id(
                "data",
                config["dataset_key"],
                dataset_status,
                now_utc(),
            ),
            "timestamp_utc": now_utc(),
            "command": command,
            "config_path": config_path,
            "config_hash": config_hash(config_path),
            "dataset_key": config["dataset_key"],
            "dataset_status": dataset_status,
            "dataset_scope": "streaming_sample",
            "model_size": "none",
            "model_config_path": "",
            "model_config_hash": "",
            "baseline_name": "data_prepare",
            "seed": config.get("sample_seed", config.get("seed", "")),
            "train_steps": 0,
            "train_tokens": manifest.get("actual_train_tokens", 0),
            "validation_tokens": manifest.get("actual_validation_tokens", 0),
            "run_status": run_status,
            "failure_reason": manifest.get("failure_reason", ""),
            "artifact_path": relative(manifest_path),
            "artifact_hash": file_hash(manifest_path),
            "environment_fingerprint_hash": environment_hash(),
            "dataset_manifest_path": relative(manifest_path),
            "metrics_path": "",
            "retention_rate": "1.0" if dataset_status == "real_nonfallback" else "",
            "evaluated_validation_tokens": 0,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    config = load_json_yaml(args.config)
    dataset_key = str(config["dataset_key"])
    command = _command(args.config, args.force)
    output_dir = root / str(config.get("output_dir", f"artifacts/data/{dataset_key}"))
    manifest_path = output_dir / "data_manifest.json"
    split_dir = output_dir / "splits"
    cached_splits_exist = all((split_dir / f"{split}.jsonl").exists() for split in ["train", "dev", "test"])

    if not args.force and manifest_path.exists() and cached_splits_exist:
        manifest = load_json_yaml(manifest_path)
        write_dataset_card(manifest, output_dir)
        _append_prepare_run(
            config=config,
            config_path=args.config,
            command=command + " # reused prepared cache",
            manifest_path=manifest_path,
            manifest=manifest,
        )
        print(f"Reused prepared streaming sample: {dataset_key}")
        print(f"Dataset status: {manifest.get('dataset_status')}")
        print(f"Manifest: {manifest_path}")
        return

    try:
        sample = load_huggingface_streaming_sample(config, root)
        seed = int(config.get("sample_seed", config.get("seed", 13)))
        splits = deterministic_split(sample.documents, seed=seed)
        manifest = _write_manifest(
            config=config,
            config_path=args.config,
            command=command,
            documents=sample.documents,
            splits=splits,
            output_dir=output_dir,
            dataset_status="real_nonfallback",
            failure_reason="",
        )
        dataset_status, failure_reason = _status_from_thresholds(manifest, config)
        if dataset_status != "real_nonfallback":
            manifest = _write_manifest(
                config=config,
                config_path=args.config,
                command=command,
                documents=sample.documents,
                splits=splits,
                output_dir=output_dir,
                dataset_status=dataset_status,
                failure_reason=failure_reason,
            )
        if dataset_status == "real_nonfallback":
            write_split_jsonl(output_dir, splits)
        else:
            # Keep the hash-bearing manifest, but do not expose insufficient splits as usable training data.
            split_dir.mkdir(parents=True, exist_ok=True)
    except StreamingDataError as exc:
        manifest = _write_manifest(
            config=config,
            config_path=args.config,
            command=command,
            documents=[],
            splits=_empty_splits(),
            output_dir=output_dir,
            dataset_status=exc.status,
            failure_reason=exc.reason,
        )
    except Exception as exc:
        manifest = _write_manifest(
            config=config,
            config_path=args.config,
            command=command,
            documents=[],
            splits=_empty_splits(),
            output_dir=output_dir,
            dataset_status="failed_due_to_environment",
            failure_reason=f"{type(exc).__name__}: {exc}",
        )

    _append_prepare_run(
        config=config,
        config_path=args.config,
        command=command,
        manifest_path=manifest_path,
        manifest=manifest,
    )
    print(f"Prepared streaming dataset state: {dataset_key}")
    print(f"Dataset status: {manifest.get('dataset_status')}")
    print(f"Dataset scope: {manifest.get('dataset_scope')}")
    print(f"Documents: {manifest.get('actual_documents')}")
    print(f"Train tokens: {manifest.get('actual_train_tokens')}")
    print(f"Validation tokens: {manifest.get('actual_validation_tokens')}")
    print(f"Failure reason: {manifest.get('failure_reason') or ''}")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
