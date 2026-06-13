from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import json
from pathlib import Path
from typing import Any

from experiment_utils import root
from models_v2.config import load_model_config
from training_v2.config import TrainingConfig
from training_v2.manifest import project_relative
from training_v2.trainer import run_training


def _read_config(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    config_path = root / path if not Path(path).is_absolute() else Path(path)
    return json.loads(config_path.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Step 5 tokenizer-aware smoke training.")
    parser.add_argument("--config", default="")
    parser.add_argument("--dataset", default="")
    parser.add_argument("--dataset-manifest", default="")
    parser.add_argument("--tokenizer-manifest", default="")
    parser.add_argument("--filter-manifest", default="")
    parser.add_argument("--model-config", default="")
    parser.add_argument("--scope", default="")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--learning-rate", type=float, default=None)
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--save-checkpoint", action="store_true")
    parser.add_argument("--device", default="")
    parser.add_argument(
        "--allow-protocol-run",
        action="store_true",
        help="Explicitly allow protocol-scope training. Step 9 keeps protocol scopes guarded by default.",
    )
    return parser.parse_args()


def _payload_from_args(args: argparse.Namespace) -> dict[str, Any]:
    payload = _read_config(args.config)
    mapping = {
        "dataset_path": args.dataset,
        "dataset_manifest_path": args.dataset_manifest,
        "tokenizer_manifest_path": args.tokenizer_manifest,
        "filter_manifest_path": args.filter_manifest,
        "model_config_path": args.model_config,
        "scope": args.scope,
        "output_dir": args.output_dir,
        "device": args.device,
    }
    for key, value in mapping.items():
        if value:
            payload[key] = value
    for key, value in {
        "seed": args.seed,
        "max_steps": args.max_steps,
        "batch_size": args.batch_size,
        "learning_rate": args.learning_rate,
    }.items():
        if value is not None:
            payload[key] = value
    if args.save_checkpoint:
        payload["save_checkpoint"] = True
    payload.setdefault("experiment_name", Path(str(payload.get("output_dir", "step5_smoke"))).name)
    payload.setdefault("filter_manifest_path", "")
    payload.setdefault("weight_decay", 0.0)
    payload.setdefault("warmup_steps", 0)
    payload.setdefault("gradient_clip", 1.0)
    payload.setdefault("eval_interval", 1)
    payload.setdefault("save_checkpoint", False)
    payload.setdefault("device", "cpu")
    payload.setdefault("precision", "float32")
    payload.setdefault("resume_from", "")
    payload.setdefault("smoke_only", payload.get("scope") == "smoke")
    payload.setdefault(
        "notes",
        "Step 5 smoke training artifact; not a main experiment or main PPL claim.",
    )
    required = [
        "dataset_path",
        "dataset_manifest_path",
        "tokenizer_manifest_path",
        "model_config_path",
        "output_dir",
        "scope",
    ]
    missing = [key for key in required if not payload.get(key)]
    if missing:
        raise SystemExit(f"Missing required training fields: {', '.join(missing)}")
    return payload


def main() -> None:
    args = _parse_args()
    payload = _payload_from_args(args)
    if payload.get("scope") in {"main_protocol", "level2_protocol", "level3_heavy_protocol"} and not args.allow_protocol_run:
        raise SystemExit("Protocol-scope training requires --allow-protocol-run and must not be confused with completed evidence.")
    training_config = TrainingConfig.from_mapping(payload)
    model_config_path = root / training_config.model_config_path if not Path(training_config.model_config_path).is_absolute() else Path(training_config.model_config_path)
    model_config = load_model_config(model_config_path)
    result = run_training(training_config=training_config, model_config=model_config, root=root)
    manifest = result["manifest"]
    manifest_path = result["manifest_path"]
    print(
        json.dumps(
            {
                "status": "completed",
                "scope": manifest["scope"],
                "smoke_only": manifest["smoke_only"],
                "experiment_name": manifest["experiment_name"],
                "manifest_path": project_relative(manifest_path, root),
                "metrics_path": manifest["metrics_path"],
                "checkpoint_path": manifest["checkpoint_path"],
                "tokens_seen": manifest["tokens_seen"],
                "train_loss_final": manifest["train_loss_final"],
                "validation_loss": manifest["validation_loss"],
                "validation_ppl": manifest["validation_ppl"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
