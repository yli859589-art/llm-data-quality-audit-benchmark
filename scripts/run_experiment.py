from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import time
from pathlib import Path

from experiment_utils import load_json_yaml, root, write_json
from registry_utils import (
    append_run,
    config_hash,
    environment_hash,
    file_hash,
    make_run_id,
    now_utc,
    relative,
)

from course_project_suite.llm_benchmark.char_lm import TrainConfig, train_character_lm
from course_project_suite.llm_benchmark.dedup import exact_deduplicate
from course_project_suite.llm_benchmark.quality import filter_by_quality
from data.real_corpora import load_documents_from_config
from data.token_counting import count_tokens
from filters.hdqspp_v2 import config_from_mapping, select_hdqspp_v2
from filters.hdqspp_v3 import (
    config_from_mapping as v3_config_from_mapping,
    select_hdqspp_v3,
)

METHOD_ALIASES = {
    "HDQS++": "hdqspp",
    "hdqs++": "hdqspp",
    "hdqspp": "hdqspp",
    "HDQS++v2": "hdqspp_v2",
    "hdqs++v2": "hdqspp_v2",
    "hdqspp_v2": "hdqspp_v2",
    "HDQS++v2-no-token-frequency": "hdqspp_v2_no_token_frequency",
    "hdqspp_v2_no_token_frequency": "hdqspp_v2_no_token_frequency",
    "v2_without_token_frequency_preservation": "hdqspp_v2_no_token_frequency",
    "HDQS++v3": "hdqspp_v3",
    "hdqs++v3": "hdqspp_v3",
    "hdqspp_v3": "hdqspp_v3",
}


def _device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _status_from_failure(exc: Exception) -> str:
    text = f"{type(exc).__name__}: {exc}".casefold()
    if "failed_due_to_network" in text or "network" in text or "connection" in text:
        return "failed_due_to_network"
    if "failed_due_to_auth" in text or "auth" in text or "permission" in text or "gated" in text:
        return "failed_due_to_auth"
    if "failed_due_to_disk" in text or "no space" in text or "disk" in text:
        return "failed_due_to_disk"
    if "out of memory" in text or "cuda" in text:
        return "failed_due_to_compute"
    if "timeout" in text:
        return "failed_due_to_timeout"
    return "failed_due_to_environment"


def _join_docs(documents: list[str]) -> str:
    return "\n\n".join(documents)


def _select_train_docs(
    baseline_name: str,
    train_documents: list[str],
    validation_documents: list[str],
    retention_ratio: float,
    seed: int,
    experiment_config: dict[str, object],
) -> tuple[list[str], float]:
    baseline_name = METHOD_ALIASES.get(baseline_name, baseline_name)
    if baseline_name == "raw":
        return list(train_documents), 1.0
    if baseline_name == "hdqspp":
        retained, _ = filter_by_quality(train_documents, retention_ratio=retention_ratio)
        return retained, len(retained) / max(1, len(train_documents))
    if baseline_name == "hdqspp_v2":
        filter_configs = experiment_config.get("filter_configs", {})
        if not isinstance(filter_configs, dict):
            filter_configs = {}
        config_path = str(filter_configs.get("hdqspp_v2", "configs/filters/hdqspp_v2.yaml"))
        v2_config = config_from_mapping(load_json_yaml(config_path))
        retained, _ = select_hdqspp_v2(
            train_documents,
            reference_documents=validation_documents,
            config=v2_config,
            variant="hdqspp_v2",
        )
        return retained, len(retained) / max(1, len(train_documents))
    if baseline_name == "hdqspp_v2_no_token_frequency":
        filter_configs = experiment_config.get("filter_configs", {})
        if not isinstance(filter_configs, dict):
            filter_configs = {}
        config_path = str(filter_configs.get("hdqspp_v2", "configs/filters/hdqspp_v2.yaml"))
        v2_config = config_from_mapping(load_json_yaml(config_path))
        retained, _ = select_hdqspp_v2(
            train_documents,
            reference_documents=validation_documents,
            config=v2_config,
            variant="v2_without_token_frequency_preservation",
        )
        return retained, len(retained) / max(1, len(train_documents))
    if baseline_name == "hdqspp_v3":
        filter_configs = experiment_config.get("filter_configs", {})
        if not isinstance(filter_configs, dict):
            filter_configs = {}
        config_path = str(filter_configs.get("hdqspp_v3", "configs/filters/hdqspp_v3.yaml"))
        v3_config = v3_config_from_mapping(load_json_yaml(config_path))
        retained, _ = select_hdqspp_v3(
            train_documents,
            reference_documents=validation_documents,
            config=v3_config,
            variant="hdqspp_v3",
            seed=seed,
        )
        return retained, len(retained) / max(1, len(train_documents))
    if baseline_name == "random_same_keep_rate":
        import random

        indexed = list(enumerate(train_documents))
        random.Random(seed).shuffle(indexed)
        keep = max(1, round(len(train_documents) * retention_ratio))
        keep_indices = {index for index, _ in indexed[:keep]}
        retained = [
            document for index, document in enumerate(train_documents) if index in keep_indices
        ]
        return retained, len(retained) / max(1, len(train_documents))
    if baseline_name == "length_filter":
        ranked = sorted(enumerate(train_documents), key=lambda row: len(row[1]), reverse=True)
        keep = max(1, round(len(train_documents) * retention_ratio))
        keep_indices = {index for index, _ in ranked[:keep]}
        retained = [
            document for index, document in enumerate(train_documents) if index in keep_indices
        ]
        return retained, len(retained) / max(1, len(train_documents))
    if baseline_name == "dedup_only":
        deduped = exact_deduplicate(train_documents).documents
        return deduped, len(deduped) / max(1, len(train_documents))
    raise ValueError(f"Unsupported experiment baseline: {baseline_name}")


def _train_config(
    experiment_config: dict[str, object],
    model_config: dict[str, object],
    seed: int,
) -> TrainConfig:
    training = experiment_config.get("training", {})
    if not isinstance(training, dict):
        training = {}
    return TrainConfig(
        block_size=int(training.get("block_size", model_config.get("context_length", 256))),
        batch_size=int(training.get("batch_size", 16)),
        steps=int(training.get("steps", 300)),
        eval_interval=int(training.get("eval_interval", 150)),
        eval_batches=int(training.get("eval_batches", 1)),
        learning_rate=float(training.get("learning_rate", 6e-4)),
        n_layer=int(model_config.get("layers", 6)),
        n_head=int(model_config.get("attention_heads", 6)),
        n_embd=int(model_config.get("hidden_size", 384)),
        seed=seed,
        device=_device(str(training.get("device", "auto"))),
    )


def _run_status(
    *,
    dataset_status: str,
    train_steps: int,
    train_tokens: int,
    validation_tokens: int,
    evaluated_validation_tokens: int,
    thresholds: dict[str, object],
) -> str:
    if dataset_status not in {"real_nonfallback", "real_local_nonfallback"}:
        return "lightweight_dev"
    if train_steps < int(thresholds.get("train_steps", 300)):
        return "lightweight_dev"
    if train_tokens < int(thresholds.get("train_tokens", 1_000_000)):
        return "lightweight_dev"
    if validation_tokens < int(thresholds.get("validation_tokens", 50_000)):
        return "lightweight_dev"
    if evaluated_validation_tokens < int(
        thresholds.get("evaluated_validation_tokens", 50_000)
    ):
        return "lightweight_dev"
    return "completed_training"


def _write_failure_run(
    *,
    command: str,
    config_path: str,
    model_path: str,
    dataset_key: str,
    dataset_status: str,
    dataset_scope: str,
    model_size: str,
    baseline_name: str,
    seed: int,
    exc: Exception,
    dataset_manifest_path: str = "",
) -> None:
    append_run(
        {
            "run_id": make_run_id(
                "train",
                dataset_key,
                model_size,
                baseline_name,
                seed,
                "failed",
                now_utc(),
            ),
            "timestamp_utc": now_utc(),
            "command": command,
            "config_path": config_path,
            "config_hash": config_hash(config_path),
            "dataset_key": dataset_key,
            "dataset_status": dataset_status,
            "dataset_scope": dataset_scope,
            "model_size": model_size,
            "model_config_path": model_path,
            "model_config_hash": config_hash(model_path),
            "baseline_name": baseline_name,
            "seed": seed,
            "train_steps": 0,
            "train_tokens": 0,
            "validation_tokens": 0,
            "run_status": _status_from_failure(exc),
            "failure_reason": f"{type(exc).__name__}: {exc}",
            "artifact_path": "",
            "artifact_hash": "",
            "environment_fingerprint_hash": environment_hash(),
            "dataset_manifest_path": dataset_manifest_path,
            "metrics_path": "",
            "final_val_loss": "",
            "final_val_perplexity": "",
            "retention_rate": "",
            "evaluated_validation_tokens": 0,
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--seeds", nargs="*", type=int, default=None)
    parser.add_argument("--methods", nargs="*", default=None)
    args = parser.parse_args()
    method_part = f" --methods {' '.join(args.methods)}" if args.methods else ""
    seed_part = f" --seeds {' '.join(str(seed) for seed in args.seeds)}" if args.seeds else ""
    command = (
        f"python scripts/run_experiment.py --config {args.config} --model {args.model}"
        f"{method_part}{seed_part}"
    )
    experiment_config = load_json_yaml(args.config)
    model_config = load_json_yaml(args.model)
    dataset_config_path = str(experiment_config["dataset_config"])
    dataset_config = load_json_yaml(dataset_config_path)
    dataset_key = str(dataset_config.get("dataset_key", Path(dataset_config_path).stem))
    seeds = args.seeds or [int(seed) for seed in experiment_config.get("seeds", [13])]
    configured_baselines = list(experiment_config.get("baselines", ["raw", "hdqspp"]))
    requested_methods = args.methods or configured_baselines
    baselines = [METHOD_ALIASES.get(str(method), str(method)) for method in requested_methods]
    model_size = str(model_config["model_key"])
    try:
        loaded = load_documents_from_config(root / dataset_config_path, root=root)
    except Exception as exc:
        manifest_path = root / "artifacts" / "data" / dataset_key / "data_manifest.json"
        dataset_status = "failed_due_to_environment"
        dataset_scope = "streaming_sample" if dataset_config.get("streaming") else "configured_not_run"
        if manifest_path.exists():
            manifest = load_json_yaml(manifest_path)
            dataset_status = str(manifest.get("dataset_status", dataset_status))
            dataset_scope = str(manifest.get("dataset_scope", dataset_scope))
        run_status = (
            dataset_status
            if dataset_status.startswith("failed_due_to_")
            else "failed_due_to_environment"
        )
        for seed in seeds:
            for baseline_name in baselines:
                append_run(
                    {
                        "run_id": make_run_id(
                            "train",
                            dataset_key,
                            model_size,
                            baseline_name,
                            seed,
                            run_status,
                            now_utc(),
                        ),
                        "timestamp_utc": now_utc(),
                        "command": command,
                        "config_path": args.config,
                        "config_hash": config_hash(args.config),
                        "dataset_key": dataset_key,
                        "dataset_status": dataset_status,
                        "dataset_scope": dataset_scope,
                        "model_size": model_size,
                        "model_config_path": args.model,
                        "model_config_hash": config_hash(args.model),
                        "baseline_name": baseline_name,
                        "seed": seed,
                        "train_steps": 0,
                        "train_tokens": 0,
                        "validation_tokens": 0,
                        "run_status": run_status,
                        "failure_reason": f"{type(exc).__name__}: {exc}",
                        "artifact_path": relative(manifest_path) if manifest_path.exists() else "",
                        "artifact_hash": file_hash(manifest_path),
                        "environment_fingerprint_hash": environment_hash(),
                        "dataset_manifest_path": relative(manifest_path) if manifest_path.exists() else "",
                        "metrics_path": "",
                        "retention_rate": "",
                        "evaluated_validation_tokens": 0,
                    }
                )
        print(f"Dataset load failed for {dataset_key}: {type(exc).__name__}: {exc}")
        print("Failure rows were appended to run_registry.jsonl.")
        return
    splits = loaded.metadata.get("predefined_splits")
    if not isinstance(splits, dict):
        raise SystemExit("run_experiment.py requires a real dataset with predefined splits.")
    train_documents = list(splits["train"])
    validation_documents = list(splits["dev"])
    test_documents = list(splits["test"])
    thresholds = experiment_config.get("completed_training_thresholds", {})
    if not isinstance(thresholds, dict):
        thresholds = {}
    dataset_status = str(loaded.metadata.get("dataset_status", "real_nonfallback"))
    dataset_scope = str(loaded.metadata.get("dataset_scope", "official_split"))
    validation_tokens = sum(count_tokens(document) for document in validation_documents)
    shared_vocab_text = _join_docs(train_documents)
    outputs = []

    for seed in seeds:
        for baseline_name in baselines:
            started = time.perf_counter()
            try:
                selected_train_documents, retention_rate = _select_train_docs(
                    str(baseline_name),
                    train_documents,
                    validation_documents,
                    float(experiment_config.get("target_keep_rate", 0.6)),
                    seed,
                    experiment_config,
                )
                train_text = _join_docs(selected_train_documents)
                validation_text = _join_docs(validation_documents)
                train_cfg = _train_config(experiment_config, model_config, seed)
                train_tokens = train_cfg.steps * train_cfg.batch_size * train_cfg.block_size
                result = train_character_lm(
                    train_text=train_text,
                    val_text=validation_text,
                    shared_vocab_text=shared_vocab_text,
                    config=train_cfg,
                )
                evaluated_validation_tokens = int(result["evaluated_validation_tokens"])
                status = _run_status(
                    dataset_status=dataset_status,
                    train_steps=train_cfg.steps,
                    train_tokens=train_tokens,
                    validation_tokens=validation_tokens,
                    evaluated_validation_tokens=evaluated_validation_tokens,
                    thresholds=thresholds,
                )
                output_dir = (
                    root
                    / "artifacts"
                    / "experiments"
                    / str(experiment_config["experiment_key"])
                    / loaded.dataset_key
                    / model_size
                    / str(baseline_name)
                    / f"seed_{seed}"
                )
                metrics_path = output_dir / "metrics.json"
                payload = {
                    "run_id": make_run_id(
                        "train",
                        loaded.dataset_key,
                        model_size,
                        baseline_name,
                        seed,
                        status,
                        now_utc(),
                    ),
                    "command": command,
                    "config_path": args.config,
                    "config_hash": config_hash(args.config),
                    "model_config_path": args.model,
                    "model_config_hash": config_hash(args.model),
                    "dataset_key": loaded.dataset_key,
                    "dataset_status": dataset_status,
                    "dataset_scope": dataset_scope,
                    "model_size": model_size,
                    "baseline_name": baseline_name,
                    "seed": seed,
                    "train_steps": train_cfg.steps,
                    "train_tokens": train_tokens,
                    "train_corpus_tokens": sum(
                        count_tokens(document) for document in selected_train_documents
                    ),
                    "validation_tokens": validation_tokens,
                    "evaluated_validation_tokens": evaluated_validation_tokens,
                    "eval_batches": result["eval_batches"],
                    "eval_batch_size": result["eval_batch_size"],
                    "eval_block_size": result["eval_block_size"],
                    "eval_token_budget": result["eval_token_budget"],
                    "eval_coverage_ratio": result["eval_coverage_ratio"],
                    "test_tokens": sum(count_tokens(document) for document in test_documents),
                    "retention_rate": retention_rate,
                    "keep_rate": retention_rate,
                    "tokenizer_type": result["tokenizer_type"],
                    "tokenizer_id": result["tokenizer_id"],
                    "tokenizer_hash": result["tokenizer_hash"],
                    "vocab_size": result["vocab_size"],
                    "parameter_count": result["parameter_count"],
                    "run_status": status,
                    "failure_reason": "",
                    "elapsed_seconds": time.perf_counter() - started,
                    "training_result": result,
                }
                write_json(metrics_path, payload)
                artifact_hash = file_hash(metrics_path)
                registry_row = {
                    **payload,
                    "timestamp_utc": now_utc(),
                    "artifact_path": relative(metrics_path),
                    "artifact_hash": artifact_hash,
                    "environment_fingerprint_hash": environment_hash(),
                    "dataset_manifest_path": relative(
                        root
                        / "artifacts"
                        / "data"
                        / loaded.dataset_key
                        / "data_manifest.json"
                    ),
                    "metrics_path": relative(metrics_path),
                    "final_val_loss": result.get("final_val_loss", ""),
                    "final_val_perplexity": result.get("final_val_perplexity", ""),
                    "final_train_loss": result.get("final_train_loss", ""),
                    "final_validation_loss": result.get("final_val_loss", ""),
                    "perplexity_or_proxy_perplexity": result.get(
                        "final_val_perplexity",
                        "",
                    ),
                    "model_quality_metric": "final_val_perplexity",
                    "privacy_metric": "",
                    "dedup_metric": "",
                }
                append_run(registry_row)
                outputs.append(payload)
                print(
                    f"seed={seed} {baseline_name}: {status}, val_ppl="
                    f"{float(result['final_val_perplexity']):.3f}, metrics={metrics_path}"
                )
            except Exception as exc:
                _write_failure_run(
                    command=command,
                    config_path=args.config,
                    model_path=args.model,
                    dataset_key=loaded.dataset_key,
                    dataset_status=dataset_status,
                    dataset_scope=dataset_scope,
                    model_size=model_size,
                    baseline_name=str(baseline_name),
                    seed=seed,
                    exc=exc,
                    dataset_manifest_path=relative(
                        root
                        / "artifacts"
                        / "data"
                        / loaded.dataset_key
                        / "data_manifest.json"
                    ),
                )
                print(f"seed={seed} {baseline_name}: failed: {type(exc).__name__}: {exc}")
    if not outputs:
        raise SystemExit(1)
    summary_path = (
        root
        / "artifacts"
        / "experiments"
        / str(experiment_config["experiment_key"])
        / loaded.dataset_key
        / model_size
        / "experiment_summary.json"
    )
    write_json(summary_path, {"runs": outputs, "command": command})
    completed = [row for row in outputs if row["run_status"] == "completed_training"]
    if len(completed) < 2:
        print("Completed-training threshold was not met for both baselines.")


if __name__ == "__main__":
    main()
