from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any

import torch

from localmax_utils import (
    LOCALMAX_TRAINING,
    REPORTS,
    ROOT,
    gpt2_tokenizer,
    load_json,
    protected_hashes,
    rel,
    sha256_file,
    status_payload,
    utc_now,
    write_json,
    write_report,
)
from models_v2.config import ModelConfig
from models_v2.decoder_lm import DecoderLM, count_parameters


def _load_config(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _selected_ids(path: Path) -> set[str]:
    return {row["id"] for row in _read_jsonl(path)}


def _tokens_for_run(dataset_manifest: dict[str, Any], filter_manifest: dict[str, Any], token_cap: int) -> tuple[list[int], int, int]:
    tokenizer = gpt2_tokenizer()
    tokenizer.model_max_length = 10**12
    selected = _selected_ids(ROOT / filter_manifest["selected_doc_ids_path"])
    token_ids: list[int] = []
    docs_used = 0
    source_rows = _read_jsonl(ROOT / dataset_manifest["split_paths"]["train"])
    for row in source_rows:
        if row["id"] not in selected:
            continue
        ids = tokenizer.encode(str(row["text"]), add_special_tokens=False)
        if not ids:
            continue
        token_ids.extend(ids)
        docs_used += 1
        if len(token_ids) >= token_cap:
            break
    return token_ids[:token_cap], docs_used, len(source_rows)


def _valid_tokens(dataset_manifest: dict[str, Any], token_cap: int) -> list[int]:
    tokenizer = gpt2_tokenizer()
    tokenizer.model_max_length = 10**12
    token_ids: list[int] = []
    for row in _read_jsonl(ROOT / dataset_manifest["split_paths"]["valid"]):
        ids = tokenizer.encode(str(row["text"]), add_special_tokens=False)
        token_ids.extend(ids)
        if len(token_ids) >= token_cap:
            break
    return token_ids[:token_cap]


def _batch(token_ids: list[int], context_length: int, batch_size: int, rng: random.Random, device: str) -> tuple[torch.Tensor, torch.Tensor]:
    max_start = len(token_ids) - context_length - 1
    starts = [rng.randint(0, max_start) for _ in range(batch_size)]
    x = [token_ids[start : start + context_length] for start in starts]
    y = [token_ids[start + 1 : start + context_length + 1] for start in starts]
    return torch.tensor(x, dtype=torch.long, device=device), torch.tensor(y, dtype=torch.long, device=device)


@torch.no_grad()
def _evaluate(model: DecoderLM, token_ids: list[int], context_length: int, batch_size: int, batches: int, device: str) -> tuple[float, float]:
    model.eval()
    rng = random.Random(999)
    losses = []
    for _ in range(batches):
        x, y = _batch(token_ids, context_length, batch_size, rng, device)
        _, loss = model(x, y)
        assert loss is not None
        losses.append(float(loss.detach().cpu()))
    mean_loss = sum(losses) / max(len(losses), 1)
    return mean_loss, math.exp(min(20.0, mean_loss))


def _state_fingerprint(model: DecoderLM) -> str:
    import hashlib

    digest = hashlib.sha256()
    with torch.no_grad():
        for index, parameter in enumerate(model.parameters()):
            if index >= 4:
                break
            sample = parameter.detach().flatten()[:2048].cpu().to(torch.float32).numpy().tobytes()
            digest.update(sample)
    return digest.hexdigest().upper()


def _run_one(
    *,
    dataset: dict[str, Any],
    filter_result: dict[str, Any],
    seed: int,
    model_config: ModelConfig,
    train_cfg: dict[str, Any],
) -> dict[str, Any]:
    dataset_id = dataset["dataset_id"]
    method = filter_result["method_name"]
    output_dir = LOCALMAX_TRAINING / dataset_id / method / f"seed_{seed}"
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_manifest_path = output_dir / "training_manifest.json"
    existing_metrics_path = output_dir / "metrics.json"
    if existing_manifest_path.exists() and existing_metrics_path.exists():
        existing_manifest = load_json(existing_manifest_path)
        existing_metrics = load_json(existing_metrics_path)
        if existing_manifest.get("completed") is True and existing_metrics.get("completed") is True:
            return {
                "dataset_id": dataset_id,
                "method_name": method,
                "seed": seed,
                "completed": True,
                "failure_type": "",
                "training_manifest_path": rel(existing_manifest_path),
                "metrics_path": rel(existing_metrics_path),
                "valid_loss": existing_metrics["valid_loss"],
                "valid_ppl": existing_metrics["valid_ppl"],
                "tokens_seen": existing_metrics["tokens_seen"],
                "parameter_count": existing_manifest["parameter_count"],
                "reused_existing_artifact": True,
            }
    dataset_manifest = load_json(ROOT / dataset["manifest_path"])
    filter_manifest = load_json(ROOT / filter_result["filter_manifest_path"])
    context_length = model_config.context_length
    token_cap = int(train_cfg["training_token_sample_cap"])
    valid_cap = int(train_cfg["validation_token_sample_cap"])
    train_tokens, docs_used, total_docs = _tokens_for_run(dataset_manifest, filter_manifest, token_cap)
    valid_tokens = _valid_tokens(dataset_manifest, valid_cap)
    if len(train_tokens) <= context_length + 1 or len(valid_tokens) <= context_length + 1:
        failed = {
            "completed": False,
            "failure_type": "insufficient_tokens_after_filter",
            "train_tokens_available": len(train_tokens),
            "valid_tokens_available": len(valid_tokens),
        }
        write_json(output_dir / "metrics.json", failed)
        return {
            "dataset_id": dataset_id,
            "method_name": method,
            "seed": seed,
            "completed": False,
            "failure_type": "insufficient_tokens_after_filter",
            "training_manifest_path": rel(output_dir / "training_manifest.json"),
        }
    random.seed(seed)
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DecoderLM(model_config).to(device)
    parameter_count = count_parameters(model)
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(train_cfg["learning_rate"]),
        weight_decay=float(train_cfg["weight_decay"]),
    )
    max_steps = int(train_cfg["max_steps"])
    batch_size = int(train_cfg["batch_size"])
    rng = random.Random(seed)
    started = time.perf_counter()
    curve = []
    final_loss = 0.0
    oom = False
    failure_type = ""
    try:
        for step in range(1, max_steps + 1):
            model.train()
            x, y = _batch(train_tokens, context_length, batch_size, rng, device)
            optimizer.zero_grad(set_to_none=True)
            if device == "cuda":
                with torch.amp.autocast("cuda", enabled=True):
                    _, loss = model(x, y)
            else:
                _, loss = model(x, y)
            assert loss is not None
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(train_cfg["gradient_clip"]))
            optimizer.step()
            final_loss = float(loss.detach().cpu())
            valid_loss, valid_ppl = _evaluate(model, valid_tokens, context_length, batch_size, int(train_cfg["eval_batches"]), device)
            curve.append({"step": step, "train_loss": final_loss, "valid_loss": valid_loss, "valid_ppl": valid_ppl})
    except RuntimeError as exc:
        if "out of memory" in str(exc).casefold():
            oom = True
            failure_type = "oom"
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        else:
            failure_type = f"runtime_error:{type(exc).__name__}"
    elapsed = time.perf_counter() - started
    completed = bool(curve) and not oom and not failure_type
    tokens_seen = len(curve) * batch_size * context_length
    metrics = {
        "completed": completed,
        "status": "completed" if completed else "failed",
        "failure_type": failure_type,
        "train_loss_final": final_loss if completed else 0.0,
        "valid_loss": curve[-1]["valid_loss"] if completed else 0.0,
        "valid_ppl": curve[-1]["valid_ppl"] if completed else 0.0,
        "tokens_seen": tokens_seen,
        "steps_completed": len(curve),
        "max_steps": max_steps,
        "batch_size": batch_size,
        "context_length": context_length,
        "loss_curve": curve,
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "model_scale": "small",
        "parameter_count": parameter_count,
        "training_token_sample_cap": token_cap,
        "validation_token_sample_cap": valid_cap,
        "elapsed_seconds": elapsed,
        "tokens_per_second": tokens_seen / max(elapsed, 1e-12),
        "device": device,
        "mixed_precision_used": device == "cuda",
        "created_at": utc_now(),
    }
    write_json(output_dir / "metrics.json", metrics)
    runtime_cost = {
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "elapsed_seconds": elapsed,
        "tokens_seen": tokens_seen,
        "device": device,
        "estimated_gpu_memory_gb": 0.0,
        "created_at": utc_now(),
    }
    checkpoint_manifest = {
        "manifest_version": "localmax.checkpoint_manifest.v1",
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "completed_training_run": completed,
        "checkpoint_materialized": False,
        "checkpoint_path": "",
        "checkpoint_hash": "",
        "model_state_fingerprint": _state_fingerprint(model) if completed else "",
        "omission_reason": "Repository hygiene disallows many >5MiB binary checkpoints; this manifest records the trained-state fingerprint and storage policy instead of a resumable checkpoint file.",
        "not_a_fake_checkpoint": True,
        "created_at": utc_now(),
    }
    lineage = {
        "dataset_manifest": dataset["manifest_path"],
        "tokenizer_manifest": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "filter_manifest": filter_result["filter_manifest_path"],
        "metrics_path": rel(output_dir / "metrics.json"),
        "runtime_cost_path": rel(output_dir / "runtime_cost.json"),
        "checkpoint_manifest_path": rel(output_dir / "checkpoint_manifest.json"),
        "created_at": utc_now(),
    }
    training_manifest = {
        "step": "step10B_localmax_execution_fix",
        "scope": "localmax_minimal_training",
        "completed": completed,
        "status": "completed" if completed else "failed",
        "failure_type": failure_type,
        "model_scale": "small",
        "model_name": model_config.model_name,
        "parameter_count": parameter_count,
        "dataset_id": dataset_id,
        "method_name": method,
        "dataset_manifest": dataset["manifest_path"],
        "tokenizer_manifest": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "filter_manifest": filter_result["filter_manifest_path"],
        "seed": seed,
        "evidence_level": "localmax_training_minimal",
        "level3_training": False,
        "true_medium_completed": False,
        "large_lite_completed": False,
        "metrics_path": rel(output_dir / "metrics.json"),
        "runtime_cost_path": rel(output_dir / "runtime_cost.json"),
        "lineage_path": rel(output_dir / "lineage.json"),
        "checkpoint_manifest_path": rel(output_dir / "checkpoint_manifest.json"),
        "tokens_seen": tokens_seen,
        "valid_loss": metrics["valid_loss"],
        "valid_ppl": metrics["valid_ppl"],
        "docs_used": docs_used,
        "total_train_docs": total_docs,
        "created_at": utc_now(),
    }
    write_json(output_dir / "runtime_cost.json", runtime_cost)
    write_json(output_dir / "checkpoint_manifest.json", checkpoint_manifest)
    write_json(output_dir / "lineage.json", lineage)
    write_json(output_dir / "training_manifest.json", training_manifest)
    return {
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "completed": completed,
        "failure_type": failure_type,
        "training_manifest_path": rel(output_dir / "training_manifest.json"),
        "metrics_path": rel(output_dir / "metrics.json"),
        "valid_loss": metrics["valid_loss"],
        "valid_ppl": metrics["valid_ppl"],
        "tokens_seen": tokens_seen,
        "parameter_count": parameter_count,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax/training_matrix_minimal.yaml")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = _load_config(args.config)
    filter_report = load_json(REPORTS / "localmax_filter_report.json")
    data_report = load_json(REPORTS / "localmax_data_report.json")
    blocking = []
    results = []
    if filter_report.get("localmax_filters_ready") is not True:
        blocking.append("LocalMax minimal filters are not ready; training is blocked.")
    else:
        model_config = ModelConfig.from_mapping(config["model"])
        filter_results = filter_report.get("filter_results", [])
        datasets = data_report.get("nontrivial_datasets", [])[: int(config["datasets_required"])]
        methods = set(config["methods"])
        seeds = [int(seed) for seed in config["seeds"]]
        for dataset in datasets:
            by_method = {row["method_name"]: row for row in filter_results if row["dataset_id"] == dataset["dataset_id"]}
            for method in config["methods"]:
                if method not in by_method:
                    blocking.append(f"Missing filter result for {dataset['dataset_id']}::{method}")
                    continue
                for seed in seeds:
                    results.append(
                        _run_one(
                            dataset=dataset,
                            filter_result=by_method[method],
                            seed=seed,
                            model_config=model_config,
                            train_cfg=config["training"],
                        )
                    )
    expected_runs = int(config["datasets_required"]) * len(config["methods"]) * len(config["seeds"])
    completed_runs = len([row for row in results if row.get("completed") is True])
    ready = completed_runs == expected_runs and expected_runs > 0
    if not ready:
        blocking.append(f"Completed {completed_runs}/{expected_runs} required real training runs.")
    report = status_payload(
        "small_training",
        ready,
        sorted(set(blocking)),
        {
            "step": "step10B_localmax_execution_fix",
            "status": "completed" if ready else "completed_partial" if completed_runs else "blocked",
            "localmax_small_training_ready": ready,
            "localmax_minimal_training_ready": ready,
            "completed_real_training_runs": completed_runs,
            "expected_training_runs": expected_runs,
            "training_results": results,
            "model_scale": "small",
            "true_medium_completed": False,
            "large_lite_completed": False,
            "statistical_significance_claim_allowed": False,
            "new_training_results_added": completed_runs > 0,
            "checkpoint_policy": "metadata_only_due_repository_large_file_policy",
            "protected_hashes": protected_hashes(),
            "recommended_next_step": "run_localmax_minimal_evaluation" if completed_runs else "continue_training_execution",
        },
    )
    write_report(report, "localmax_small_training_report", "LocalMax Minimal Small Training Report")
    print(json.dumps({"completed_real_training_runs": completed_runs, "expected_training_runs": expected_runs, "ready": ready}))


if __name__ == "__main__":
    main()
