from __future__ import annotations

import argparse
import json
import math
import random
import time
from pathlib import Path
from typing import Any

import torch

from localmax_utils import ROOT, gpt2_tokenizer, load_json, protected_hashes, rel, status_payload, utc_now, write_json, write_report
from models_v2.config import ModelConfig
from models_v2.decoder_lm import DecoderLM, count_parameters


OUTPUT_ROOT = ROOT / "artifacts" / "localmax_training_strengthened"


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


def _encode_until(tokenizer: Any, rows: list[dict[str, Any]], cap: int, selected: set[str] | None = None) -> tuple[list[int], int]:
    token_ids: list[int] = []
    docs_used = 0
    for row in rows:
        if selected is not None and row["id"] not in selected:
            continue
        ids = tokenizer.encode(str(row["text"]), add_special_tokens=False)
        if not ids:
            continue
        token_ids.extend(ids)
        docs_used += 1
        if len(token_ids) >= cap:
            break
    return token_ids[:cap], docs_used


def _batch(token_ids: list[int], context_length: int, batch_size: int, rng: random.Random, device: str) -> tuple[torch.Tensor, torch.Tensor]:
    max_start = len(token_ids) - context_length - 1
    starts = [rng.randint(0, max_start) for _ in range(batch_size)]
    x = [token_ids[start : start + context_length] for start in starts]
    y = [token_ids[start + 1 : start + context_length + 1] for start in starts]
    return torch.tensor(x, dtype=torch.long, device=device), torch.tensor(y, dtype=torch.long, device=device)


@torch.no_grad()
def _evaluate_full_sample(model: DecoderLM, token_ids: list[int], context_length: int, batch_size: int, device: str) -> float:
    model.eval()
    losses = []
    usable = min(len(token_ids) - context_length - 1, 32768)
    starts = list(range(0, max(1, usable), context_length))
    for offset in range(0, len(starts), batch_size):
        batch_starts = starts[offset : offset + batch_size]
        x = [token_ids[start : start + context_length] for start in batch_starts]
        y = [token_ids[start + 1 : start + context_length + 1] for start in batch_starts]
        xb = torch.tensor(x, dtype=torch.long, device=device)
        yb = torch.tensor(y, dtype=torch.long, device=device)
        _, loss = model(xb, yb)
        assert loss is not None
        losses.append(float(loss.detach().cpu()))
    return sum(losses) / max(len(losses), 1)


def _ppl_fields(valid_loss: float) -> dict[str, Any]:
    clipped = valid_loss > 20.0
    return {
        "valid_ppl_raw": None if clipped else math.exp(valid_loss),
        "valid_ppl_clipped": math.exp(20.0 if clipped else valid_loss),
        "ppl_clipped": clipped,
        "ppl_comparable": not clipped,
        "metric_for_comparison": "valid_loss",
    }


def _state_fingerprint(model: DecoderLM) -> str:
    import hashlib

    digest = hashlib.sha256()
    with torch.no_grad():
        for index, parameter in enumerate(model.parameters()):
            if index >= 4:
                break
            digest.update(parameter.detach().flatten()[:2048].cpu().to(torch.float32).numpy().tobytes())
    return digest.hexdigest().upper()


def _runtime_device() -> tuple[str, bool, float]:
    cuda = torch.cuda.is_available()
    if not cuda:
        return "cpu", False, 0.0
    props = torch.cuda.get_device_properties(0)
    return "cuda", True, round(float(props.total_memory) / (1024**3), 2)


def _existing_result(output_dir: Path, min_tokens: int, min_steps: int, context_length: int) -> dict[str, Any] | None:
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
        and int(metrics.get("steps_completed", 0)) >= min_steps
        and int(metrics.get("context_length", 0)) >= context_length
        and manifest.get("evidence_level") == "localmax_training_strengthened"
    ):
        return {
            "dataset_id": manifest["dataset_id"],
            "method_name": manifest["method_name"],
            "seed": manifest["seed"],
            "completed": True,
            "failed": False,
            "training_manifest_path": rel(manifest_path),
            "metrics_path": rel(metrics_path),
            "valid_loss": metrics["valid_loss"],
            "valid_ppl_clipped": metrics["valid_ppl_clipped"],
            "ppl_clipped": metrics["ppl_clipped"],
            "ppl_comparable": metrics["ppl_comparable"],
            "tokens_seen": metrics["tokens_seen"],
            "steps_completed": metrics["steps_completed"],
            "parameter_count": manifest["parameter_count"],
            "min_training_strength_met": True,
            "reused_existing_artifact": True,
        }
    return None


def _run_one(
    *,
    dataset_id: str,
    method: str,
    seed: int,
    model_config: ModelConfig,
    training_cfg: dict[str, Any],
    tokenizer: Any,
    token_cache: dict[tuple[str, str], tuple[list[int], list[int], int]],
) -> dict[str, Any]:
    output_dir = OUTPUT_ROOT / dataset_id / method / f"seed_{seed}"
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = _existing_result(
        output_dir,
        int(training_cfg["min_tokens_seen_per_run"]),
        int(training_cfg["max_steps"]),
        model_config.context_length,
    )
    if existing:
        return existing
    cache_key = (dataset_id, method)
    if cache_key not in token_cache:
        dataset_manifest = load_json(ROOT / "artifacts" / "localmax_data" / dataset_id / "dataset_manifest.json")
        filter_manifest = load_json(ROOT / "artifacts" / "localmax_filters" / dataset_id / method / "filter_manifest.json")
        selected = _selected_ids(ROOT / filter_manifest["selected_doc_ids_path"])
        train_rows = _read_jsonl(ROOT / dataset_manifest["split_paths"]["train"])
        valid_rows = _read_jsonl(ROOT / dataset_manifest["split_paths"]["valid"])
        train_tokens, docs_used = _encode_until(tokenizer, train_rows, int(training_cfg["training_token_sample_cap"]), selected)
        valid_tokens, _ = _encode_until(tokenizer, valid_rows, int(training_cfg["validation_token_sample_cap"]), None)
        token_cache[cache_key] = (train_tokens, valid_tokens, docs_used)
    train_tokens, valid_tokens, docs_used = token_cache[cache_key]
    random.seed(seed)
    torch.manual_seed(seed)
    device, cuda_available, gpu_memory_gb = _runtime_device()
    model = DecoderLM(model_config).to(device)
    parameter_count = count_parameters(model)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(training_cfg["learning_rate"]), weight_decay=float(training_cfg["weight_decay"]))
    max_steps = int(training_cfg["max_steps"])
    batch_size = int(training_cfg["batch_size"])
    grad_accum = int(training_cfg["gradient_accumulation_steps"])
    context_length = model_config.context_length
    rng = random.Random(seed)
    curve = []
    started = time.perf_counter()
    oom = False
    failure_type = ""
    final_train_loss = 0.0
    try:
        for step in range(1, max_steps + 1):
            model.train()
            optimizer.zero_grad(set_to_none=True)
            step_losses = []
            for _ in range(grad_accum):
                x, y = _batch(train_tokens, context_length, batch_size, rng, device)
                if device == "cuda" and bool(training_cfg.get("mixed_precision", True)):
                    with torch.amp.autocast("cuda", enabled=True):
                        _, loss = model(x, y)
                else:
                    _, loss = model(x, y)
                assert loss is not None
                (loss / grad_accum).backward()
                step_losses.append(float(loss.detach().cpu()))
            torch.nn.utils.clip_grad_norm_(model.parameters(), float(training_cfg["gradient_clip"]))
            optimizer.step()
            final_train_loss = sum(step_losses) / max(len(step_losses), 1)
            if step in {1, 25, 50, 75, max_steps}:
                curve.append({"step": step, "train_loss": final_train_loss})
    except RuntimeError as exc:
        if "out of memory" in str(exc).casefold():
            oom = True
            failure_type = "oom"
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        else:
            failure_type = f"runtime_error:{type(exc).__name__}"
    steps_completed = max_steps if not failure_type else (curve[-1]["step"] if curve else 0)
    tokens_seen = steps_completed * batch_size * context_length * grad_accum
    valid_loss = _evaluate_full_sample(model, valid_tokens, context_length, batch_size, device) if steps_completed else 0.0
    ppl = _ppl_fields(valid_loss) if steps_completed else {
        "valid_ppl_raw": None,
        "valid_ppl_clipped": 0.0,
        "ppl_clipped": False,
        "ppl_comparable": False,
        "metric_for_comparison": "valid_loss",
    }
    min_strength = (
        not failure_type
        and tokens_seen >= int(training_cfg["min_tokens_seen_per_run"])
        and steps_completed >= max_steps
        and context_length >= 128
        and int(training_cfg["validation_token_sample_cap"]) >= 32768
    )
    completed = min_strength
    elapsed = time.perf_counter() - started
    metrics = {
        "completed": completed,
        "failed": not completed,
        "failure_type": failure_type,
        "min_training_strength_met": min_strength,
        "steps_completed": steps_completed,
        "max_steps": max_steps,
        "context_length": context_length,
        "batch_size": batch_size,
        "gradient_accumulation_steps": grad_accum,
        "tokens_seen": tokens_seen,
        "train_loss_final": final_train_loss,
        "valid_loss": valid_loss,
        **ppl,
        "validation_token_sample_cap": int(training_cfg["validation_token_sample_cap"]),
        "training_token_sample_cap": int(training_cfg["training_token_sample_cap"]),
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
        "cuda_available": cuda_available,
        "gpu_memory_gb": gpu_memory_gb,
        "duration_seconds": elapsed,
        "oom": oom,
        "early_stopped": False,
        "tokens_seen": tokens_seen,
        "created_at": utc_now(),
    }
    checkpoint_manifest = {
        "manifest_version": "localmax.strengthened.checkpoint_manifest.v1",
        "completed_training_run": completed,
        "checkpoint_policy": str(training_cfg.get("checkpoint_policy", "metadata_only_due_repository_large_file_policy")),
        "checkpoint_materialized": False,
        "checkpoint_path": "",
        "checkpoint_hash": "",
        "model_state_fingerprint": _state_fingerprint(model) if completed else "",
        "not_a_fake_checkpoint": True,
        "omission_reason": "Repository hygiene disallows many large binary checkpoints; strengthened evidence records metrics, lineage, and trained-state fingerprint.",
        "created_at": utc_now(),
    }
    lineage = {
        "dataset_manifest": f"artifacts/localmax_data/{dataset_id}/dataset_manifest.json",
        "tokenizer_manifest": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "filter_manifest": f"artifacts/localmax_filters/{dataset_id}/{method}/filter_manifest.json",
        "previous_minimal_training_manifest": f"artifacts/localmax_training/{dataset_id}/{method}/seed_{seed}/training_manifest.json",
        "metrics_path": rel(output_dir / "metrics.json"),
        "runtime_cost_path": rel(output_dir / "runtime_cost.json"),
        "checkpoint_manifest_path": rel(output_dir / "checkpoint_manifest.json"),
        "created_at": utc_now(),
    }
    training_manifest = {
        "step": "step10B_localmax_training_strengthen",
        "scope": "localmax_training_strengthened",
        "completed": completed,
        "failed": not completed,
        "failure_type": failure_type,
        "evidence_level": "localmax_training_strengthened",
        "previous_minimal_run_superseded": True,
        "level3_training": False,
        "true_medium_completed": False,
        "large_lite_completed": False,
        "model_scale": "small",
        "model_name": model_config.model_name,
        "parameter_count": parameter_count,
        "dataset_id": dataset_id,
        "method_name": method,
        "dataset_manifest": f"artifacts/localmax_data/{dataset_id}/dataset_manifest.json",
        "tokenizer_manifest": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "filter_manifest": f"artifacts/localmax_filters/{dataset_id}/{method}/filter_manifest.json",
        "seed": seed,
        "tokens_seen": tokens_seen,
        "steps_completed": steps_completed,
        "min_training_strength_met": min_strength,
        "metrics_path": rel(output_dir / "metrics.json"),
        "runtime_cost_path": rel(output_dir / "runtime_cost.json"),
        "lineage_path": rel(output_dir / "lineage.json"),
        "checkpoint_manifest_path": rel(output_dir / "checkpoint_manifest.json"),
        "valid_loss": valid_loss,
        "valid_ppl_clipped": ppl["valid_ppl_clipped"],
        "ppl_clipped": ppl["ppl_clipped"],
        "ppl_comparable": ppl["ppl_comparable"],
        "metric_for_comparison": "valid_loss",
        "created_at": utc_now(),
    }
    write_json(output_dir / "metrics.json", metrics)
    write_json(output_dir / "runtime_cost.json", runtime_cost)
    write_json(output_dir / "checkpoint_manifest.json", checkpoint_manifest)
    write_json(output_dir / "lineage.json", lineage)
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
        "valid_loss": valid_loss,
        "valid_ppl_clipped": ppl["valid_ppl_clipped"],
        "ppl_clipped": ppl["ppl_clipped"],
        "ppl_comparable": ppl["ppl_comparable"],
        "tokens_seen": tokens_seen,
        "steps_completed": steps_completed,
        "parameter_count": parameter_count,
        "min_training_strength_met": min_strength,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax/training_strengthened.yaml")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = _load_config(args.config)
    model_config = ModelConfig.from_mapping(config["model"])
    tokenizer = gpt2_tokenizer()
    tokenizer.model_max_length = 10**12
    token_cache: dict[tuple[str, str], tuple[list[int], list[int], int]] = {}
    results = []
    for dataset_id in config["datasets"]:
        for method in config["methods"]:
            for seed in config["seeds"]:
                results.append(
                    _run_one(
                        dataset_id=str(dataset_id),
                        method=str(method),
                        seed=int(seed),
                        model_config=model_config,
                        training_cfg=config["training"],
                        tokenizer=tokenizer,
                        token_cache=token_cache,
                    )
                )
    expected = len(config["datasets"]) * len(config["methods"]) * len(config["seeds"])
    completed = [row for row in results if row["completed"] is True and row["min_training_strength_met"] is True]
    failed = [row for row in results if row["completed"] is not True]
    full = len(completed) == expected
    partial = 16 <= len(completed) < expected
    blocking = []
    if not full:
        blocking.append(f"Strengthened training completed {len(completed)}/{expected} required runs.")
    report = status_payload(
        "training_strengthened",
        full,
        blocking,
        {
            "step": "step10B_localmax_training_strengthen",
            "status": "completed" if full else "completed_partial" if partial else "completed_with_failures",
            "training_strengthened_completed": full,
            "training_strengthened_partial": partial,
            "completed_strengthened_runs": len(completed),
            "expected_strengthened_runs": expected,
            "failed_or_partial_runs": len(failed),
            "min_tokens_seen_per_completed_run": min([int(row["tokens_seen"]) for row in completed], default=0),
            "min_steps_completed": min([int(row["steps_completed"]) for row in completed], default=0),
            "context_length": model_config.context_length,
            "validation_token_sample_cap": int(config["training"]["validation_token_sample_cap"]),
            "model_scale": "small",
            "parameter_count": completed[0]["parameter_count"] if completed else model_config.parameter_count,
            "true_medium_completed": False,
            "large_lite_completed": False,
            "official_downstream_completed": False,
            "training_results": results,
            "protected_hashes": protected_hashes(),
            "recommended_next_step": "run_localmax_strengthened_evaluation" if completed else "continue_step10B_localmax_training_strengthen",
        },
    )
    write_report(report, "localmax_training_strengthened_report", "LocalMax Training Strengthened Report")
    print(json.dumps({"completed_strengthened_runs": len(completed), "expected_strengthened_runs": expected, "full": full}))


if __name__ == "__main__":
    main()

