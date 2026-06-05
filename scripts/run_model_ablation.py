from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import csv
import json
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
    read_registry_jsonl,
    relative,
)

from course_project_suite.llm_benchmark.char_lm import TrainConfig, train_character_lm
from data.real_corpora import load_documents_from_config
from data.token_counting import count_tokens
from filters.hdqspp_v2 import config_from_mapping, select_hdqspp_v2

TOP5_VARIANTS = [
    ("ablation_v2_full", "hdqspp_v2"),
    ("ablation_v2_without_length_prior", "v2_without_length_prior"),
    ("ablation_v2_without_distribution_preservation", "v2_without_distribution_preservation"),
    ("ablation_v2_without_token_frequency_preservation", "v2_without_token_frequency_preservation"),
    ("ablation_v2_without_repetition_penalty", "v2_without_repetition_penalty"),
]
DEFERRED_VARIANTS = [
    "ablation_v2_without_quality_diversity_balance",
    "ablation_v2_hard_filtering",
    "ablation_v2_soft_weighting_curriculum",
]


def _device(requested: str) -> str:
    if requested != "auto":
        return requested
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _join_docs(documents: list[str]) -> str:
    return "\n\n".join(documents)


def _train_config(
    experiment_config: dict[str, object],
    model_config: dict[str, object],
) -> TrainConfig:
    training = experiment_config.get("training", {})
    if not isinstance(training, dict):
        training = {}
    return TrainConfig(
        block_size=int(training.get("block_size", model_config.get("context_length", 256))),
        batch_size=int(training.get("batch_size", 16)),
        steps=int(training.get("steps", 300)),
        eval_interval=int(training.get("eval_interval", 300)),
        eval_batches=int(training.get("eval_batches", 13)),
        learning_rate=float(training.get("learning_rate", 6e-4)),
        n_layer=int(model_config.get("layers", 6)),
        n_head=int(model_config.get("attention_heads", 6)),
        n_embd=int(model_config.get("hidden_size", 384)),
        seed=1,
        device=_device(str(training.get("device", "auto"))),
    )


def _latest_reference_rows() -> dict[str, dict[str, str]]:
    references = {}
    for row in read_registry_jsonl():
        if row["dataset_key"] != "wikitext2_paper" or row["model_size"] != "small":
            continue
        if row["seed"] != "1" or row["run_status"] != "completed_training":
            continue
        if row["baseline_name"] in {"random_same_keep_rate", "dedup_only"}:
            references[row["baseline_name"]] = row
    return references


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _figure(rows: list[dict[str, object]], path: Path) -> None:
    values = [
        (str(row["ablation_name"]), float(row["final_val_perplexity"]))
        for row in rows
        if row["run_status"] in {"completed_training", "reference_completed_training"}
    ]
    if not values:
        return
    max_value = max(value for _, value in values)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="980" height="360">',
        "<desc>source=artifacts/ablations/model_training_ablation_results.csv</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="32" font-family="Arial" font-size="18">Model-training ablation PPL</text>',
    ]
    for index, (name, value) in enumerate(values):
        y = 64 + index * 34
        width = 620 * value / max_value
        lines.append(f'<text x="24" y="{y + 16}" font-family="Arial" font-size="11">{name}</text>')
        lines.append(f'<rect x="310" y="{y}" width="{width:.1f}" height="22" fill="#4c78a8"/>')
        lines.append(
            f'<text x="{320 + width:.1f}" y="{y + 15}" '
            f'font-family="Arial" font-size="11">{value:.3f}</text>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    args = parser.parse_args()
    experiment_config = load_json_yaml(args.config)
    model_path = str(experiment_config.get("model_config", "configs/models/small.yaml"))
    model_config = load_json_yaml(model_path)
    loaded = load_documents_from_config(root / experiment_config["dataset_config"], root=root)
    splits = loaded.metadata.get("predefined_splits")
    if not isinstance(splits, dict):
        raise SystemExit("Model ablation requires predefined WikiText-2 splits.")
    train_documents = list(splits["train"])
    validation_documents = list(splits["dev"])
    shared_vocab_text = _join_docs(train_documents)
    validation_text = _join_docs(validation_documents)
    validation_tokens = sum(count_tokens(document) for document in validation_documents)
    cfg = _train_config(experiment_config, model_config)
    train_tokens = cfg.steps * cfg.batch_size * cfg.block_size
    v2_config = config_from_mapping(load_json_yaml("configs/filters/hdqspp_v2.yaml"))
    output_dir = root / "artifacts" / "ablations"
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []

    for ablation_name, variant in TOP5_VARIANTS:
        started = time.perf_counter()
        selected, _ = select_hdqspp_v2(
            train_documents,
            reference_documents=validation_documents,
            config=v2_config,
            variant=variant,
        )
        result = train_character_lm(
            train_text=_join_docs(selected),
            val_text=validation_text,
            shared_vocab_text=shared_vocab_text,
            config=cfg,
        )
        run_id = make_run_id(
            "model_ablation",
            loaded.dataset_key,
            "small",
            ablation_name,
            1,
            "completed_training",
            now_utc(),
        )
        metrics_path = output_dir / "model_training" / ablation_name / "seed_1" / "metrics.json"
        payload = {
            "run_id": run_id,
            "ablation_name": ablation_name,
            "variant": variant,
            "run_status": "completed_training",
            "seed": 1,
            "retention_rate": len(selected) / max(1, len(train_documents)),
            "train_tokens": train_tokens,
            "validation_tokens": validation_tokens,
            "evaluated_validation_tokens": result["evaluated_validation_tokens"],
            "tokenizer_hash": result["tokenizer_hash"],
            "vocab_size": result["vocab_size"],
            "parameter_count": result["parameter_count"],
            "final_val_perplexity": result["final_val_perplexity"],
            "elapsed_seconds": time.perf_counter() - started,
            "training_result": result,
        }
        write_json(metrics_path, payload)
        append_run(
            {
                "run_id": run_id,
                "timestamp_utc": now_utc(),
                "command": f"python scripts/run_model_ablation.py --config {args.config}",
                "config_path": args.config,
                "config_hash": config_hash(args.config),
                "dataset_key": loaded.dataset_key,
                "dataset_status": str(loaded.metadata.get("dataset_status")),
                "dataset_scope": str(loaded.metadata.get("dataset_scope")),
                "model_size": "small",
                "model_config_path": model_path,
                "model_config_hash": config_hash(model_path),
                "baseline_name": ablation_name,
                "seed": 1,
                "train_steps": cfg.steps,
                "train_tokens": train_tokens,
                "validation_tokens": validation_tokens,
                "run_status": "completed_training",
                "failure_reason": "",
                "artifact_path": relative(metrics_path),
                "artifact_hash": file_hash(metrics_path),
                "environment_fingerprint_hash": environment_hash(),
                "dataset_manifest_path": "artifacts/data/wikitext2_paper/data_manifest.json",
                "metrics_path": relative(metrics_path),
                "final_val_loss": result["final_val_loss"],
                "final_val_perplexity": result["final_val_perplexity"],
                "retention_rate": payload["retention_rate"],
                "tokenizer_type": result["tokenizer_type"],
                "tokenizer_id": result["tokenizer_id"],
                "tokenizer_hash": result["tokenizer_hash"],
                "vocab_size": result["vocab_size"],
                "parameter_count": result["parameter_count"],
                "evaluated_validation_tokens": result["evaluated_validation_tokens"],
                "eval_batches": result["eval_batches"],
                "eval_batch_size": result["eval_batch_size"],
                "eval_block_size": result["eval_block_size"],
                "eval_token_budget": result["eval_token_budget"],
                "eval_coverage_ratio": result["eval_coverage_ratio"],
                "final_train_loss": result["final_train_loss"],
                "final_validation_loss": result["final_val_loss"],
                "perplexity_or_proxy_perplexity": result["final_val_perplexity"],
                "model_quality_metric": "model_training_ablation_final_val_perplexity",
                "keep_rate": payload["retention_rate"],
            }
        )
        rows.append({key: value for key, value in payload.items() if key != "training_result"})
        print(
            f"{ablation_name}: completed_training, "
            f"val_ppl={float(result['final_val_perplexity']):.3f}"
        )

    references = _latest_reference_rows()
    for name, row in references.items():
        rows.append(
            {
                "run_id": row["run_id"],
                "ablation_name": name,
                "variant": "reference_existing_training",
                "run_status": "reference_completed_training",
                "seed": row["seed"],
                "retention_rate": row["retention_rate"],
                "train_tokens": row["train_tokens"],
                "validation_tokens": row["validation_tokens"],
                "evaluated_validation_tokens": row["evaluated_validation_tokens"],
                "tokenizer_hash": row["tokenizer_hash"],
                "vocab_size": row["vocab_size"],
                "parameter_count": row["parameter_count"],
                "final_val_perplexity": row["final_val_perplexity"],
            }
        )

    deferred_path = output_dir / "model_training_ablation_configured_not_run.json"
    deferred_payload = [
        {
            "ablation_name": name,
            "run_status": "configured_not_run",
            "reason": "Compute-limited Stage 2.5 run completed top 5 ablations only.",
        }
        for name in DEFERRED_VARIANTS
    ]
    deferred_path.write_text(
        json.dumps(deferred_payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    for item in deferred_payload:
        append_run(
            {
                "run_id": make_run_id(
                    "model_ablation",
                    item["ablation_name"],
                    "configured_not_run",
                    now_utc(),
                ),
                "timestamp_utc": now_utc(),
                "command": f"python scripts/run_model_ablation.py --config {args.config}",
                "config_path": args.config,
                "config_hash": config_hash(args.config),
                "dataset_key": loaded.dataset_key,
                "dataset_status": str(loaded.metadata.get("dataset_status")),
                "dataset_scope": str(loaded.metadata.get("dataset_scope")),
                "model_size": "small",
                "model_config_path": model_path,
                "model_config_hash": config_hash(model_path),
                "baseline_name": item["ablation_name"],
                "seed": "",
                "train_steps": 0,
                "train_tokens": 0,
                "validation_tokens": 0,
                "run_status": "configured_not_run",
                "failure_reason": item["reason"],
                "artifact_path": relative(deferred_path),
                "artifact_hash": file_hash(deferred_path),
                "environment_fingerprint_hash": environment_hash(),
                "dataset_manifest_path": "artifacts/data/wikitext2_paper/data_manifest.json",
                "metrics_path": relative(deferred_path),
            }
        )

    csv_path = output_dir / "model_training_ablation_results.csv"
    json_path = output_dir / "model_training_ablation_results.json"
    md_path = output_dir / "model_training_ablation_summary.md"
    _write_csv(csv_path, rows)
    json_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(
        "# Model-Training Ablation Summary\n\n"
        "Top 5 HDQS++ v2 ablations were trained with the same small-model budget. "
        "Deferred variants are recorded separately as configured_not_run.\n\n"
        "| Ablation | Status | Seed | PPL |\n"
        "|---|---|---:|---:|\n"
        + "\n".join(
            f"| {row['ablation_name']} | {row['run_status']} | {row['seed']} | "
            f"{float(row['final_val_perplexity']):.3f} |"
            for row in rows
            if row["run_status"] in {"completed_training", "reference_completed_training"}
        )
        + "\n",
        encoding="utf-8",
    )
    _figure(rows, root / "artifacts" / "figures" / "model_ablation_effects.svg")
    print(f"Model-training ablation rows: {len(rows)}")
    print(f"Model-training ablation CSV: {csv_path}")


if __name__ == "__main__":
    main()
