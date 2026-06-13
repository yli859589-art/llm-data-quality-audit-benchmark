from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ARTIFACT_TYPES = {
    "dataset_manifest",
    "tokenizer_manifest",
    "filter_manifest",
    "training_manifest",
    "checkpoint_manifest",
    "evaluation_manifest",
    "mechanism_manifest",
    "readiness_report",
    "claim_map",
    "main_table",
    "smoke_output",
    "protocol_output",
    "historical_main_result",
    "level3_main_result",
    "figure",
    "report",
}


@dataclass(frozen=True)
class ArtifactRecord:
    artifact_id: str
    artifact_type: str
    path: str
    hash: str
    created_at: str
    step: str
    scope: str
    dataset_name: str = ""
    method_name: str = ""
    model_name: str = ""
    tokenizer_name: str = ""
    evidence_level: str = "unknown"
    smoke_only: bool = False
    protocol_only: bool = False
    completed: bool = False
    main_evidence: bool = False
    level3_evidence: bool = False
    parent_artifacts: list[str] = field(default_factory=list)
    derived_artifacts: list[str] = field(default_factory=list)
    claim_ids: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

