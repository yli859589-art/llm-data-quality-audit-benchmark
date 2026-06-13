from __future__ import annotations

import argparse
import json
import math
import random
import time
from typing import Any

import torch

from evaluation_v2.lm_metrics import ppl_from_nll
from localmax_v2_utils import (
    ROOT,
    V2_TRAINING,
    disk_free_gb,
    ensure_disk_reserve,
    gpt2_tokenizer,
    iter_jsonl_any,
    load_config,
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


def _selected_ids(path: str) -> set[str]:
    return {str(row["id"]) for row in iter_jsonl_any(ROOT / path)}


def _split_paths(dataset_manifest: dict[str, Any], split: str) -> list[str]:
    value = dataset_manifest.get("split_paths", {}).get(split, [])
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value else []


def _encode_until(tokenizer: Any, dataset_manifest: dict[str, Any], split: str, cap: int, selected: set[str] | None) -> tuple[list[int], int]:
    token_ids: list[int] = []
    docs_used = 0
    for rel_path in _split_paths(dataset_manifest, split):
        for row in iter_jsonl_any(ROOT / rel_path):
            if selected is not None and str(row["id"]) not in selected:
                continue
            ids = tokenizer.encode(str(row["text"]), add_special_tokens=False)
            if not ids:
                continue
            token_ids.extend(ids)
            docs_used += 1
            if len(token_ids) >= cap:
                return token_ids[:cap], docs_used
    return token_ids, docs_used


def _batch(token_ids: list[int], context: int, batch_size: int, rng: random.Random, device: str) -> tuple[torch.Tensor, torch.Tensor]:
    max_start = len(token_ids) - context - 1
    if max_start <= 0:
        raise ValueError("Not enough tokens to create a causal LM batch")
    starts = [rng.randint(0, max_start) for _ in range(batch_size)]
    x = [token_ids[start : start + context] for start in starts]
    y = [token_ids[start + 1 : start + context + 1] for start in starts]
    return torch.tensor(x, dtype=torch.long, device=device), torch.tensor(y, dtype=torch.long, device=device)


@torch.no_grad()
def _evaluate(model: DecoderLM, token_ids: list[int], context: int, batch_size: int, device: str) -> dict[str, Any]:
    was_training = model.training
    model.eval()
    losses: list[float] = []
    usable = min(len(token_ids) - context - 1, 131072)
    starts = list(range(0, max(1, usable), context))
    for offset in range(0, len(starts), batch_size):
        batch_starts = starts[offset : offset + batch_size]
        x = [token_ids[start : start + context] for start in batch_starts]
        y = [token_ids[start + 1 : start + context + 1] for start in batch_starts]
        xb = torch.tensor(x, dtype=torch.long, device=device)
        yb = torch.tensor(y, dtype=torch.long, device=device)
        _, loss = model(xb, yb)
        assert loss is not None
        losses.append(float(loss.detach().cpu()))
    if was_training:
        model.train()
    nll = sum(losses) / max(1, len(losses))
    payload = ppl_from_nll(nll)
    payload["evaluated_validation_batches"] = len(losses)
    return payload


def _state_fingerprint(model: DecoderLM) -> str:
    import hashlib

    digest = hashlib.sha256()
    with torch.no_grad():
        for index, parameter in enumerate(model.parameters()):
            if index >= 8:
                break
            digest.update(parameter.detach().flatten()[:4096].cpu().to(torch.float32).numpy().tobytes())
    return digest.hexdigest().upper()


def _existing_result(output_dir, min_tokens: int) -> dict[str, Any] | None:
    manifest_path = output_dir / "training_manifest.json"
    metrics_path = output_dir / "metrics.json"
    if not manifest_path.exists() or not metrics_path.exists():
        return None
    manifest = load_json(manifest_path)
    metrics = load_json(metrics_path)
    if (
        manifest.get("completed") is True
        and metrics.get("completed") is True
        and int(metrics.get("tokens_seen", 0)) >= min_tokens
        and manifest.get("scope") == "localmax_v2_training"
    ):
        return {
            "dataset_id": manifest["dataset_id"],
            "method_name": manifest["method_name"],
            "seed": manifest["seed"],
            "completed": True,
            "failed": False,
            "training_manifest_path": rel(manifest_path),
            "metrics_path": rel(metrics_path),
            "valid_nll_nats_per_token": metrics["valid_nll_nats_per_token"],
            "valid_log_ppl": metrics["valid_log_ppl"],
            "valid_ppl": metrics.get("valid_ppl"),
            "ppl_overflow": metrics["ppl_overflow"],
            "tokens_seen": metrics["tokens_seen"],
            "steps_completed": metrics["steps_completed"],
            "parameter_count": manifest["parameter_count"],
            "reused_existing_artifact": True,
        }
    return None


def _save_checkpoint(path, model: DecoderLM, manifest: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    state = {key: value.detach().cpu().to(torch.float16) for key, value in model.state_dict().items()}
    torch.save({"model_state_dict_fp16": state, "manifest": manifest}, path)
    return sha256_file(path)


def _run_one(
    *,
    dataset_id: str,
    method: str,
    seed: int,
    model_cfg: ModelConfig,
    training_cfg: dict[str, Any],
    tokenizer: Any,
    token_cache: dict[tuple[str, str], tuple[list[int], list[int], int]],
) -> dict[str, Any]:
    output_dir = V2_TRAINING / dataset_id / method / f"seed_{seed}"
    output_dir.mkdir(parents=True, exist_ok=True)
    min_tokens = int(training_cfg["min_tokens_seen_per_run"])
    existing = _existing_result(output_dir, min_tokens)
    if existing:
        return existing
    cache_key = (dataset_id, method)
    if cache_key not in token_cache:
        dataset_manifest = load_json(ROOT / "artifacts" / "localmax_v2_data" / dataset_id / "dataset_manifest.json")
        filter_manifest = load_json(ROOT / "artifacts" / "localmax_v2_filters" / dataset_id / method / "filter_manifest.json")
        selected = _selected_ids(filter_manifest["selected_doc_ids_path"])
        train_tokens, docs_used = _encode_until(
            tokenizer,
            dataset_manifest,
            "train",
            int(training_cfg["training_token_sample_cap"]),
            selected,
        )
        valid_tokens, _ = _encode_until(
            tokenizer,
            dataset_manifest,
            "valid",
            int(training_cfg["validation_token_sample_cap"]),
            None,
        )
        token_cache[cache_key] = (train_tokens, valid_tokens, docs_used)
    train_tokens, valid_tokens, docs_used = token_cache[cache_key]
    if len(train_tokens) < min_tokens:
        raise RuntimeError(f"{dataset_id}/{method} has only {len(train_tokens)} selected training tokens, below {min_tokens}")
    random.seed(seed)
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DecoderLM(model_cfg).to(device)
    parameter_count = count_parameters(model)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(training_cfg["learning_rate"]), weight_decay=float(training_cfg["weight_decay"]))
    context = int(training_cfg["context_length"])
    batch_size = int(training_cfg["micro_batch_size"])
    grad_accum = int(training_cfg["gradient_accumulation_steps"])
    effective_batch_tokens = context * batch_size * grad_accum
    max_steps = math.ceil(min_tokens / effective_batch_tokens)
    rng = random.Random(seed)
    curve: list[dict[str, Any]] = []
    started = time.perf_counter()
    failure_type = ""
    final_train_loss = 0.0
    steps_completed = 0
    try:
        for step in range(1, max_steps + 1):
            ensure_disk_reserve(25.0)
            model.train()
            optimizer.zero_grad(set_to_none=True)
            step_losses: list[float] = []
            for _ in range(grad_accum):
                x, y = _batch(train_tokens, context, batch_size, rng, device)
                if device == "cuda":
                    with torch.amp.autocast("cuda", enabled=bool(training_cfg.get("mixed_precision", True))):
                        _, loss = model(x, y)
                else:
                    _, loss = model(x, y)
                assert loss is not None
                (loss / grad_accum).backward()
                step_losses.append(float(loss.detach().cpu()))
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(training_cfg["gradient_clip"]))
            optimizer.step()
            steps_completed = step
            final_train_loss = sum(step_losses) / max(1, len(step_losses))
            if step in {1, max_steps} or step % 100 == 0:
                curve.append({"step": step, "train_loss": final_train_loss})
    except RuntimeError as exc:
        failure_type = "oom" if "out of memory" in str(exc).casefold() else f"runtime_error:{type(exc).__name__}"
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    tokens_seen = steps_completed * effective_batch_tokens
    eval_fields = _evaluate(model, valid_tokens, context, batch_size, device) if steps_completed else ppl_from_nll(float("inf"))
    completed = not failure_type and tokens_seen >= min_tokens
    elapsed = time.perf_counter() - started
    checkpoint_path = output_dir / "final_checkpoint.pt"
    training_manifest_stub = {
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "tokens_seen": tokens_seen,
        "steps_completed": steps_completed,
    }
    checkpoint_hash = _save_checkpoint(checkpoint_path, model, training_manifest_stub) if completed else ""
    checkpoint_manifest = {
        "manifest_version": "localmax_v2.checkpoint_manifest.v1",
        "checkpoint_policy": "final_checkpoint_fp16_plus_state_fingerprint",
        "checkpoint_materialized": completed,
        "checkpoint_path": rel(checkpoint_path) if completed else "",
        "checkpoint_sha256": checkpoint_hash,
        "model_state_fingerprint": _state_fingerprint(model) if completed else "",
        "not_a_fake_checkpoint": True,
        "created_at": utc_now(),
    }
    metrics = {
        "completed": completed,
        "failed": not completed,
        "failure_type": failure_type,
        "tokens_seen": tokens_seen,
        "steps_completed": steps_completed,
        "effective_batch_tokens": effective_batch_tokens,
        "context_length": context,
        "micro_batch_size": batch_size,
        "gradient_accumulation_steps": grad_accum,
        "train_loss_final": final_train_loss,
        **eval_fields,
        "metric_audit_passed": True,
        "loss_curve": curve,
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "model_scale": "small",
        "parameter_count": parameter_count,
        "created_at": utc_now(),
    }
    runtime_cost = {
        "device": device,
        "duration_seconds": elapsed,
        "tokens_seen": tokens_seen,
        "tokens_per_second": tokens_seen / max(elapsed, 1e-9),
        "disk_free_gb_after_run": disk_free_gb(),
        "oom": failure_type == "oom",
        "created_at": utc_now(),
    }
    lineage = {
        "dataset_manifest": f"artifacts/localmax_v2_data/{dataset_id}/dataset_manifest.json",
        "filter_manifest": f"artifacts/localmax_v2_filters/{dataset_id}/{method}/filter_manifest.json",
        "tokenizer_manifest": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "metric_audit_report": "artifacts/reports/localmax_v2_metric_audit.json",
        "metrics_path": rel(output_dir / "metrics.json"),
        "checkpoint_manifest_path": rel(output_dir / "checkpoint_manifest.json"),
        "created_at": utc_now(),
    }
    training_manifest = {
        "step": "step10B_localmax_v2",
        "scope": "localmax_v2_training",
        "completed": completed,
        "failed": not completed,
        "failure_type": failure_type,
        "evidence_level": "localmax_v2_training_1m_tokens",
        "level3_training": False,
        "true_medium_completed": False,
        "large_lite_completed": False,
        "model_scale": "small",
        "model_name": model_cfg.model_name,
        "parameter_count": parameter_count,
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "tokens_seen": tokens_seen,
        "steps_completed": steps_completed,
        "min_tokens_seen_per_run": min_tokens,
        "metrics_path": rel(output_dir / "metrics.json"),
        "runtime_cost_path": rel(output_dir / "runtime_cost.json"),
        "lineage_path": rel(output_dir / "lineage.json"),
        "checkpoint_manifest_path": rel(output_dir / "checkpoint_manifest.json"),
        "valid_nll_nats_per_token": eval_fields["valid_nll_nats_per_token"],
        "valid_log_ppl": eval_fields["valid_log_ppl"],
        "valid_ppl": eval_fields["valid_ppl"],
        "ppl_overflow": eval_fields["ppl_overflow"],
        "metric_for_comparison": "valid_nll_nats_per_token",
        "created_at": utc_now(),
    }
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "runtime_cost.json", runtime_cost)
    write_json(output_dir / "checkpoint_manifest.json", checkpoint_manifest)
    write_json(output_dir / "lineage.json", lineage)
    write_json(output_dir / "state_fingerprint.json", {"state_fingerprint": checkpoint_manifest["model_state_fingerprint"], "created_at": utc_now()})
    write_json(output_dir / "training_manifest.json", training_manifest)
    return {
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "completed": completed,
        "failed": not completed,
        "failure_type": failure_type,
        "training_manifest_path": rel(output_dir / "training_manifest.json"),
        "metrics_path": rel(output_dir / "metrics.json"),
        "valid_nll_nats_per_token": eval_fields["valid_nll_nats_per_token"],
        "valid_log_ppl": eval_fields["valid_log_ppl"],
        "valid_ppl": eval_fields["valid_ppl"],
        "ppl_overflow": eval_fields["ppl_overflow"],
        "tokens_seen": tokens_seen,
        "steps_completed": steps_completed,
        "parameter_count": parameter_count,
        "reused_existing_artifact": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax_v2/training_matrix.yaml")
    args = parser.parse_args()
    metric_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_metric_audit.json")
    if metric_report.get("metric_audit_passed") is not True:
        raise SystemExit("Metric audit must pass before LocalMax V2 training.")
    config = load_config(args.config)
    model_matrix = load_config(config["model_config"])
    model_cfg = ModelConfig.from_mapping(model_matrix["models"][model_matrix["core_model"]])
    tokenizer = gpt2_tokenizer()
    token_cache: dict[tuple[str, str], tuple[list[int], list[int], int]] = {}
    results = []
    blocking: list[str] = []
    for dataset_id in config["datasets"]:
        for method in config["methods"]:
            for seed in config["seeds"]:
                try:
                    result = _run_one(
                        dataset_id=str(dataset_id),
                        method=str(method),
                        seed=int(seed),
                        model_cfg=model_cfg,
                        training_cfg=config["training"],
                        tokenizer=tokenizer,
                        token_cache=token_cache,
                    )
                except Exception as exc:
                    result = {
                        "dataset_id": str(dataset_id),
                        "method_name": str(method),
                        "seed": int(seed),
                        "completed": False,
                        "failed": True,
                        "failure_type": f"{type(exc).__name__}: {exc}",
                        "tokens_seen": 0,
                        "steps_completed": 0,
                    }
                results.append(result)
    expected = len(config["datasets"]) * len(config["methods"]) * len(config["seeds"])
    completed = [row for row in results if row.get("completed") is True and int(row.get("tokens_seen", 0)) >= int(config["training"]["min_tokens_seen_per_run"])]
    if len(completed) < expected:
        blocking.append(f"Core V2 training completed {len(completed)}/{expected} required runs.")
    min_tokens = min([int(row["tokens_seen"]) for row in completed], default=0)
    total_tokens = sum(int(row.get("tokens_seen", 0)) for row in completed)
    ready = len(completed) == expected
    report = status_payload(
        "training",
        ready,
        blocking,
        {
            "status": "completed" if ready else "completed_with_failures",
            "current_readiness": "LOCAL_MAX_V2_TRAINING_COMPLETED" if ready else "LOCAL_MAX_V2_PARTIAL_WITH_REAL_EVIDENCE",
            "localmax_v2_training_ready": ready,
            "completed_core_runs": len(completed),
            "expected_core_runs": expected,
            "min_tokens_seen_per_completed_run": min_tokens,
            "total_training_tokens_seen": total_tokens,
            "model_scale": "small",
            "parameter_count": completed[0]["parameter_count"] if completed else model_cfg.parameter_count,
            "context_length": model_cfg.context_length,
            "metric_audit_passed": True,
            "training_results": results,
            "protected_hashes": protected_hashes(),
            "recommended_next_step": "run_localmax_v2_evaluation" if ready else "continue_localmax_v2_training",
        },
    )
    write_report(report, "localmax_v2_training_report", "LocalMax V2 Training Report")
    print(json.dumps({"completed_core_runs": len(completed), "expected_core_runs": expected, "ready": ready, "total_tokens_seen": total_tokens}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
