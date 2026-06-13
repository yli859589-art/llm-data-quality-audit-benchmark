from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .schema import PROTOCOL_SCOPES, VALID_EVALUATION_TYPES, VALID_SCOPES


@dataclass(frozen=True)
class EvaluationConfig:
    evaluation_name: str
    evaluation_type: str
    scope: str
    method_name: str
    dataset_name: str
    input_artifact_path: str = ""
    input_manifest_path: str = ""
    training_manifest_path: str = ""
    filter_manifest_path: str = ""
    tokenizer_manifest_path: str = ""
    metrics: list[str] = field(default_factory=list)
    seed: int = 42
    bootstrap_samples: int = 200
    smoke_only: bool = False
    protocol_only: bool = False
    notes: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "EvaluationConfig":
        config = cls(
            evaluation_name=str(payload["evaluation_name"]),
            evaluation_type=str(payload["evaluation_type"]),
            scope=str(payload["scope"]),
            method_name=str(payload["method_name"]),
            dataset_name=str(payload["dataset_name"]),
            input_artifact_path=str(payload.get("input_artifact_path", "")),
            input_manifest_path=str(payload.get("input_manifest_path", "")),
            training_manifest_path=str(payload.get("training_manifest_path", "")),
            filter_manifest_path=str(payload.get("filter_manifest_path", "")),
            tokenizer_manifest_path=str(payload.get("tokenizer_manifest_path", "")),
            metrics=[str(item) for item in payload.get("metrics", [])],
            seed=int(payload.get("seed", 42)),
            bootstrap_samples=int(payload.get("bootstrap_samples", 200)),
            smoke_only=bool(payload.get("smoke_only", False)),
            protocol_only=bool(payload.get("protocol_only", False)),
            notes=str(payload.get("notes", "")),
        )
        validate_evaluation_config(config)
        return config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationInput:
    payload: dict[str, Any]


@dataclass(frozen=True)
class EvaluationResult:
    evaluation_name: str
    evaluation_type: str
    method_name: str
    dataset_name: str
    scope: str
    metrics: dict[str, Any]
    summary: dict[str, Any]
    input_hashes: dict[str, str]
    output_paths: dict[str, str]
    smoke_only: bool
    protocol_only: bool
    completed: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseEvaluator:
    evaluation_type = "base"

    def __init__(self, config: EvaluationConfig) -> None:
        self.config = config

    def run(self, root):
        raise NotImplementedError


def validate_evaluation_config(config: EvaluationConfig) -> None:
    if config.evaluation_type not in VALID_EVALUATION_TYPES:
        raise ValueError(f"invalid evaluation_type: {config.evaluation_type}")
    if config.scope not in VALID_SCOPES:
        raise ValueError(f"invalid scope: {config.scope}")
    if config.scope == "smoke" and not config.smoke_only:
        raise ValueError("smoke evaluation must set smoke_only=true")
    if config.scope in PROTOCOL_SCOPES and not config.protocol_only:
        raise ValueError("protocol evaluation must set protocol_only=true")
    if config.scope == "completed_run" and config.smoke_only:
        raise ValueError("completed_run cannot be smoke_only")
