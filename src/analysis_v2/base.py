from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .schema import PROTOCOL_SCOPES, VALID_ANALYSIS_TYPES, VALID_SCOPES


def _listify(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item)]
    return [str(value)]


@dataclass(frozen=True)
class MechanismAnalysisConfig:
    analysis_name: str
    analysis_type: str
    scope: str
    dataset_name: str
    methods: list[str] = field(default_factory=list)
    input_artifact_paths: list[str] = field(default_factory=list)
    input_manifest_paths: list[str] = field(default_factory=list)
    training_manifest_paths: list[str] = field(default_factory=list)
    filter_manifest_paths: list[str] = field(default_factory=list)
    evaluation_manifest_paths: list[str] = field(default_factory=list)
    tokenizer_manifest_paths: list[str] = field(default_factory=list)
    output_dir: str = ""
    smoke_only: bool = False
    protocol_only: bool = False
    insufficient_evidence_policy: str = "mark_explicitly"
    notes: str = ""

    @classmethod
    def from_mapping(cls, payload: dict[str, Any]) -> "MechanismAnalysisConfig":
        config = cls(
            analysis_name=str(payload["analysis_name"]),
            analysis_type=str(payload["analysis_type"]),
            scope=str(payload["scope"]),
            dataset_name=str(payload["dataset_name"]),
            methods=_listify(payload.get("methods", [])),
            input_artifact_paths=_listify(payload.get("input_artifact_paths", [])),
            input_manifest_paths=_listify(payload.get("input_manifest_paths", [])),
            training_manifest_paths=_listify(payload.get("training_manifest_paths", [])),
            filter_manifest_paths=_listify(payload.get("filter_manifest_paths", [])),
            evaluation_manifest_paths=_listify(payload.get("evaluation_manifest_paths", [])),
            tokenizer_manifest_paths=_listify(payload.get("tokenizer_manifest_paths", [])),
            output_dir=str(payload.get("output_dir", "")),
            smoke_only=bool(payload.get("smoke_only", False)),
            protocol_only=bool(payload.get("protocol_only", False)),
            insufficient_evidence_policy=str(payload.get("insufficient_evidence_policy", "mark_explicitly")),
            notes=str(payload.get("notes", "")),
        )
        validate_mechanism_config(config)
        return config

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MechanismAnalysisInput:
    payload: dict[str, Any]


@dataclass(frozen=True)
class MechanismAnalysisResult:
    analysis_name: str
    analysis_type: str
    scope: str
    dataset_name: str
    methods: list[str]
    summary: dict[str, Any]
    diagnostics: list[dict[str, Any]]
    evidence_sufficiency: str
    input_hashes: dict[str, str]
    output_paths: dict[str, str]
    smoke_only: bool
    protocol_only: bool
    insufficient_evidence: bool
    claim_allowed: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class BaseMechanismAnalyzer:
    analysis_type = "base"

    def __init__(self, config: MechanismAnalysisConfig) -> None:
        self.config = config

    def run(self, output_dir: Path, root: Path) -> MechanismAnalysisResult:
        raise NotImplementedError


def validate_mechanism_config(config: MechanismAnalysisConfig) -> None:
    if config.analysis_type not in VALID_ANALYSIS_TYPES:
        raise ValueError(f"invalid analysis_type: {config.analysis_type}")
    if config.scope not in VALID_SCOPES:
        raise ValueError(f"invalid scope: {config.scope}")
    if config.scope == "smoke" and not config.smoke_only:
        raise ValueError("smoke mechanism analysis must set smoke_only=true")
    if config.scope in PROTOCOL_SCOPES and not config.protocol_only:
        raise ValueError("protocol mechanism analysis must set protocol_only=true")
    if config.scope == "completed_run" and (config.smoke_only or config.protocol_only):
        raise ValueError("completed_run cannot be smoke_only or protocol_only")

