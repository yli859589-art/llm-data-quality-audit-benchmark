from __future__ import annotations

import argparse
import json
import math
import random
import time
from typing import Any

import torch

from ccfc_utils import (
    CCFC_FILTERS,
    CCFC_TRAINING,
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
from evaluation_v2.lm_metrics import ppl_from_nll
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
    valid_nll = metrics.get("valid_nll_nats_per_token")
    finite_metric = isinstance(valid_nll, (int, float)) and math.isfinite(float(valid_nll))
    if (
        manifest.get("completed") is True
        and metrics.get("completed") is True
        and int(metrics.get("tokens_seen", 0)) >= min_tokens
        and manifest.get("scope") == "ccfc_training_matrix"
        and finite_metric
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


def _load_v2_warm_start(model: DecoderLM, dataset_id: str, method: str, seed: int) -> tuple[int, int, str]:
    checkpoint = V2_TRAINING / dataset_id / method / f"seed_{seed}" / "final_checkpoint.pt"
    metrics = V2_TRAINING / dataset_id / method / f"seed_{seed}" / "metrics.json"
    if not checkpoint.exists() or not metrics.exists():
        return 0, 0, ""
    payload = torch.load(checkpoint, map_location="cpu")
    state = payload.get("model_state_dict_fp16")
    if not isinstance(state, dict):
        return 0, 0, ""
    model.load_state_dict({key: value.to(torch.float32) for key, value in state.items()}, strict=True)
    metric_payload = load_json(metrics)
    return int(metric_payload.get("tokens_seen", 0)), int(metric_payload.get("steps_completed", 0)), rel(checkpoint)


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
) -> dict[str, Any]:
    output_dir = CCFC_TRAINING / dataset_id / method / f"seed_{seed}"
    output_dir.mkdir(parents=True, exist_ok=True)
    min_tokens = int(training_cfg["min_tokens_seen_per_run"])
    existing = _existing_result(output_dir, min_tokens)
    if existing:
        return existing
    dataset_manifest = load_json(ROOT / "artifacts" / "localmax_v2_data" / dataset_id / "dataset_manifest.json")
    filter_manifest = load_json(CCFC_FILTERS / dataset_id / method / "filter_manifest.json")
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
    if len(train_tokens) < min_tokens:
        raise RuntimeError(f"{dataset_id}/{method} has only {len(train_tokens)} selected training tokens, below {min_tokens}")
    random.seed(seed)
    torch.manual_seed(seed)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = DecoderLM(model_cfg).to(device)
    warm_tokens = 0
    warm_steps = 0
    warm_checkpoint = ""
    if bool(training_cfg.get("resume_from_localmax_v2_if_available", True)):
        warm_tokens, warm_steps, warm_checkpoint = _load_v2_warm_start(model, dataset_id, method, seed)
        model = model.to(device)
    parameter_count = count_parameters(model)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(training_cfg["learning_rate"]), weight_decay=float(training_cfg["weight_decay"]))
    context = int(training_cfg["context_length"])
    batch_size = int(training_cfg["micro_batch_size"])
    grad_accum = int(training_cfg["gradient_accumulation_steps"])
    effective_batch_tokens = context * batch_size * grad_accum
    remaining_tokens = max(0, min_tokens - warm_tokens)
    additional_steps = math.ceil(remaining_tokens / effective_batch_tokens)
    rng = random.Random(seed + 9973)
    curve: list[dict[str, Any]] = []
    started = time.perf_counter()
    failure_type = ""
    final_train_loss = 0.0
    local_steps_completed = 0
    try:
        for step in range(1, additional_steps + 1):
            ensure_disk_reserve(float(training_cfg.get("disk_reserve_gb", 20)))
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
            local_steps_completed = step
            final_train_loss = sum(step_losses) / max(1, len(step_losses))
            global_step = warm_steps + step
            if step in {1, additional_steps} or step % 250 == 0:
                curve.append({"step": global_step, "train_loss": final_train_loss, "tokens_seen": warm_tokens + step * effective_batch_tokens})
    except RuntimeError as exc:
        failure_type = "oom" if "out of memory" in str(exc).casefold() else f"runtime_error:{type(exc).__name__}"
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    tokens_seen = warm_tokens + local_steps_completed * effective_batch_tokens
    steps_completed = warm_steps + local_steps_completed
    eval_fields = _evaluate(model, valid_tokens, context, batch_size, device) if steps_completed else ppl_from_nll(float("inf"))
    finite_eval = isinstance(eval_fields.get("valid_nll_nats_per_token"), (int, float)) and math.isfinite(float(eval_fields["valid_nll_nats_per_token"]))
    if not finite_eval and not failure_type:
        failure_type = "nonfinite_validation_metric"
    completed = not failure_type and tokens_seen >= min_tokens and finite_eval
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
        "manifest_version": "localmax_ccfc.checkpoint_manifest.v1",
        "checkpoint_policy": "final_checkpoint_fp16_plus_state_fingerprint",
        "checkpoint_materialized": completed,
        "checkpoint_path": rel(checkpoint_path) if completed else "",
        "checkpoint_sha256": checkpoint_hash,
        "model_state_fingerprint": _state_fingerprint(model) if completed else "",
        "warm_start_checkpoint": warm_checkpoint,
        "not_a_fake_checkpoint": True,
        "created_at": utc_now(),
    }
    metrics = {
        "completed": completed,
        "failed": not completed,
        "failure_type": failure_type,
        "tokens_seen": tokens_seen,
        "warm_start_tokens_seen": warm_tokens,
        "additional_tokens_seen": local_steps_completed * effective_batch_tokens,
        "steps_completed": steps_completed,
        "additional_steps_completed": local_steps_completed,
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
        "additional_tokens_seen": local_steps_completed * effective_batch_tokens,
        "tokens_per_second": (local_steps_completed * effective_batch_tokens) / max(elapsed, 1e-9),
        "disk_free_gb_after_run": disk_free_gb(),
        "oom": failure_type == "oom",
        "created_at": utc_now(),
    }
    lineage = {
        "dataset_manifest": f"artifacts/localmax_v2_data/{dataset_id}/dataset_manifest.json",
        "filter_manifest": f"artifacts/localmax_ccfc_filters/{dataset_id}/{method}/filter_manifest.json",
        "warm_start_checkpoint": warm_checkpoint,
        "tokenizer_manifest": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "metric_audit_report": "artifacts/reports/localmax_v2_metric_audit.json",
        "metrics_path": rel(output_dir / "metrics.json"),
        "checkpoint_manifest_path": rel(output_dir / "checkpoint_manifest.json"),
        "created_at": utc_now(),
    }
    training_manifest = {
        "step": "localmax_ccfc_strengthening",
        "scope": "ccfc_training_matrix",
        "completed": completed,
        "failed": not completed,
        "failure_type": failure_type,
        "evidence_level": "ccfc_candidate_training_5m_tokens",
        "ccf_c_paper_claimed": False,
        "ccf_b_ready_claimed": False,
        "level3_training": False,
        "model_scale": "small",
        "model_name": model_cfg.model_name,
        "parameter_count": parameter_count,
        "dataset_id": dataset_id,
        "method_name": method,
        "seed": seed,
        "tokens_seen": tokens_seen,
        "warm_start_tokens_seen": warm_tokens,
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
        "warm_start_checkpoint": warm_checkpoint,
        "reused_existing_artifact": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax_ccfc/training_matrix.yaml")
    parser.add_argument("--max-runs", type=int, default=0, help="Optional smoke limit; 0 means full matrix.")
    parser.add_argument("--max-new-runs", type=int, default=0, help="Train at most this many missing runs; existing completed runs are still counted.")
    parser.add_argument("--dataset", default="", help="Optional dataset_id filter.")
    parser.add_argument("--method", default="", help="Optional method_name filter.")
    parser.add_argument("--seed", type=int, default=0, help="Optional seed filter.")
    args = parser.parse_args()
    metric_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_metric_audit.json")
    if metric_report.get("metric_audit_passed") is not True:
        raise SystemExit("Metric audit must pass before CCF-C strengthened training.")
    config = load_config(args.config)
    model_matrix = load_config(config["model_config"])
    model_cfg = ModelConfig.from_mapping(model_matrix["models"][model_matrix["core_model"]])
    tokenizer = gpt2_tokenizer()
    jobs = [
        (str(dataset_id), str(method), int(seed))
        for dataset_id in config["datasets"]
        for method in config["methods"]
        for seed in config["seeds"]
    ]
    if args.dataset:
        jobs = [job for job in jobs if job[0] == args.dataset]
    if args.method:
        jobs = [job for job in jobs if job[1] == args.method]
    if args.seed:
        jobs = [job for job in jobs if job[2] == args.seed]
    if args.max_runs:
        jobs = jobs[: args.max_runs]
    results = []
    blocking: list[str] = []
    new_runs_started = 0
    min_tokens_required = int(config["training"]["min_tokens_seen_per_run"])
    for dataset_id, method, seed in jobs:
        output_dir = CCFC_TRAINING / dataset_id / method / f"seed_{seed}"
        existing = _existing_result(output_dir, min_tokens_required)
        if existing:
            print(f"SKIP completed {dataset_id}/{method}/seed_{seed} tokens={existing['tokens_seen']}", flush=True)
            results.append(existing)
            continue
        if args.max_new_runs and new_runs_started >= args.max_new_runs:
            print(f"DEFER missing {dataset_id}/{method}/seed_{seed} because --max-new-runs={args.max_new_runs}", flush=True)
            continue
        print(f"RUN missing {dataset_id}/{method}/seed_{seed}", flush=True)
        new_runs_started += 1
        try:
            result = _run_one(
                dataset_id=dataset_id,
                method=method,
                seed=seed,
                model_cfg=model_cfg,
                training_cfg=config["training"],
                tokenizer=tokenizer,
            )
            if result.get("completed") is True:
                print(
                    f"OK completed {dataset_id}/{method}/seed_{seed} "
                    f"tokens={result.get('tokens_seen')} steps={result.get('steps_completed')}",
                    flush=True,
                )
            else:
                print(f"FAILED incomplete {dataset_id}/{method}/seed_{seed} {result.get('failure_type')}", flush=True)
        except Exception as exc:
            result = {
                "dataset_id": dataset_id,
                "method_name": method,
                "seed": seed,
                "completed": False,
                "failed": True,
                "failure_type": f"{type(exc).__name__}: {exc}",
                "tokens_seen": 0,
                "steps_completed": 0,
            }
            print(f"FAILED exception {dataset_id}/{method}/seed_{seed}: {type(exc).__name__}: {exc}", flush=True)
        results.append(result)
    expected = len(config["datasets"]) * len(config["methods"]) * len(config["seeds"])
    completed = [row for row in results if row.get("completed") is True and int(row.get("tokens_seen", 0)) >= int(config["training"]["min_tokens_seen_per_run"])]
    full_matrix_attempted = len(results) == expected
    if len(completed) < expected:
        blocking.append(f"CCF-C strengthened training completed {len(completed)}/{expected} required runs.")
    if args.max_runs:
        blocking.append(f"Smoke-limited training run used --max-runs={args.max_runs}; full matrix not attempted.")
    if args.max_new_runs:
        blocking.append(f"Continuation-limited training run used --max-new-runs={args.max_new_runs}; full matrix may not be attempted in this invocation.")
    min_tokens = min([int(row["tokens_seen"]) for row in completed], default=0)
    total_tokens = sum(int(row.get("tokens_seen", 0)) for row in completed)
    ready = len(completed) == expected
    report = status_payload(
        "training",
        ready,
        blocking,
        {
            "status": "completed" if ready else "completed_with_failures",
            "current_readiness": "CCFC_TRAINING_COMPLETED" if ready else "CCFC_PARTIAL_EVIDENCE",
            "ccfc_training_ready": ready,
            "completed_core_runs": len(completed),
            "expected_core_runs": expected,
            "runs_attempted": len(results),
            "new_runs_started": new_runs_started,
            "full_matrix_attempted": full_matrix_attempted,
            "min_tokens_seen_per_completed_run": min_tokens,
            "target_tokens_seen_per_run": int(config["training"]["target_tokens_seen_per_run"]),
            "total_training_tokens_seen": total_tokens,
            "model_scale": "small",
            "parameter_count": completed[0]["parameter_count"] if completed else model_cfg.parameter_count,
            "context_length": model_cfg.context_length,
            "metric_audit_passed": True,
            "training_results": results,
            "protected_hashes": protected_hashes(),
            "recommended_next_step": "run_ccfc_evaluation" if ready else "continue_ccfc_training",
        },
    )
    write_report(report, "localmax_ccfc_training_report", "LocalMax CCF-C Strengthened Training Report")
    print(json.dumps({"completed_core_runs": len(completed), "expected_core_runs": expected, "ready": ready, "total_tokens_seen": total_tokens}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
