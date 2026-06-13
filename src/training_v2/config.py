from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

VALID_TRAINING_SCOPES = {
    "smoke",
    "sample",
    "main_protocol",
    "level2_protocol",
    "level3_heavy_protocol",
    "completed_run",
}


@dataclass(frozen=True)
class TrainingConfig:
    experiment_name: str
    dataset_path: str
    dataset_manifest_path: str
    tokenizer_manifest_path: str
    filter_manifest_path: str
    model_config_path: str
    output_dir: str
    scope: str
    seed: int
    max_steps: int
    batch_size: int
    learning_rate: float
    weight_decay: float
    warmup_steps: int
    gradient_clip: float
    eval_interval: int
    save_checkpoint: bool
    device: str
    precision: str
    resume_from: str
    smoke_only: bool
    notes: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "TrainingConfig":
        config = cls(
            experiment_name=str(payload["experiment_name"]),
            dataset_path=str(payload["dataset_path"]),
            dataset_manifest_path=str(payload["dataset_manifest_path"]),
            tokenizer_manifest_path=str(payload["tokenizer_manifest_path"]),
            filter_manifest_path=str(payload.get("filter_manifest_path", "")),
            model_config_path=str(payload["model_config_path"]),
            output_dir=str(payload["output_dir"]),
            scope=str(payload["scope"]),
            seed=int(payload.get("seed", 42)),
            max_steps=int(payload.get("max_steps", 2)),
            batch_size=int(payload.get("batch_size", 2)),
            learning_rate=float(payload.get("learning_rate", 0.001)),
            weight_decay=float(payload.get("weight_decay", 0.0)),
            warmup_steps=int(payload.get("warmup_steps", 0)),
            gradient_clip=float(payload.get("gradient_clip", 1.0)),
            eval_interval=int(payload.get("eval_interval", 1)),
            save_checkpoint=bool(payload.get("save_checkpoint", False)),
            device=str(payload.get("device", "cpu")),
            precision=str(payload.get("precision", "float32")),
            resume_from=str(payload.get("resume_from", "")),
            smoke_only=bool(payload.get("smoke_only", False)),
            notes=str(payload.get("notes", "")),
        )
        from .validation import validate_training_config

        validate_training_config(config)
        return config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_training_config(path: str | Path) -> TrainingConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("training config must contain a JSON-compatible mapping")
    return TrainingConfig.from_mapping(payload)
