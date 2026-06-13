from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .parameter_count import estimate_decoder_lm_parameters

VALID_SCALE_CLASSES = {"tiny_smoke", "small", "medium_protocol", "large_lite_protocol"}


@dataclass(frozen=True)
class ModelConfig:
    model_name: str
    model_family: str
    vocab_size: int
    context_length: int
    num_layers: int
    hidden_size: int
    num_heads: int
    dropout: float
    tie_embeddings: bool
    parameter_count: int
    scale_class: str
    notes: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "ModelConfig":
        parameter_count = int(payload.get("parameter_count") or 0)
        if parameter_count <= 0:
            parameter_count = estimate_decoder_lm_parameters(
                vocab_size=int(payload["vocab_size"]),
                context_length=int(payload["context_length"]),
                num_layers=int(payload["num_layers"]),
                hidden_size=int(payload["hidden_size"]),
                num_heads=int(payload["num_heads"]),
                tie_embeddings=bool(payload.get("tie_embeddings", True)),
            )
        config = cls(
            model_name=str(payload["model_name"]),
            model_family=str(payload.get("model_family", "decoder_lm")),
            vocab_size=int(payload["vocab_size"]),
            context_length=int(payload["context_length"]),
            num_layers=int(payload["num_layers"]),
            hidden_size=int(payload["hidden_size"]),
            num_heads=int(payload["num_heads"]),
            dropout=float(payload.get("dropout", 0.0)),
            tie_embeddings=bool(payload.get("tie_embeddings", True)),
            parameter_count=parameter_count,
            scale_class=str(payload["scale_class"]),
            notes=str(payload.get("notes", "")),
        )
        from .validation import validate_model_config

        validate_model_config(config)
        return config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_model_config(path: str | Path) -> ModelConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("model config must contain a JSON-compatible mapping")
    return ModelConfig.from_mapping(payload)
