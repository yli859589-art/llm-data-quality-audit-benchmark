from __future__ import annotations

from enum import Enum
from typing import Any

from .schema import PROTOCOL_SCOPES


class EvidenceLevel(str, Enum):
    NONE = "none"
    SMOKE_ONLY = "smoke_only"
    PROTOCOL_ONLY = "protocol_only"
    SAMPLE_PARTIAL = "sample_partial"
    HISTORICAL_MAIN_ONLY = "historical_main_only"
    LEVEL2_CANDIDATE = "level2_candidate"
    LEVEL3_COMPLETED = "level3_completed"


def assess_evidence(
    *,
    scope: str,
    sample_size: int | None = None,
    smoke_only: bool = False,
    protocol_only: bool = False,
    required_future_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    required = required_future_artifacts or []
    if smoke_only or scope == "smoke":
        return {
            "evidence_level": EvidenceLevel.SMOKE_ONLY.value,
            "evidence_sufficiency": "smoke_diagnostic_only",
            "insufficient_evidence": True,
            "claim_allowed": False,
            "required_future_artifacts": required,
            "warning": "smoke_output_is_not_main_evidence",
        }
    if protocol_only or scope in PROTOCOL_SCOPES:
        return {
            "evidence_level": EvidenceLevel.PROTOCOL_ONLY.value,
            "evidence_sufficiency": "protocol_only",
            "insufficient_evidence": True,
            "claim_allowed": False,
            "required_future_artifacts": required,
            "warning": "protocol_only_no_completed_run",
        }
    if sample_size is None or sample_size < 30:
        return {
            "evidence_level": EvidenceLevel.SAMPLE_PARTIAL.value,
            "evidence_sufficiency": "insufficient",
            "insufficient_evidence": True,
            "claim_allowed": False,
            "required_future_artifacts": required,
            "warning": "insufficient_sample_size",
        }
    return {
        "evidence_level": EvidenceLevel.LEVEL2_CANDIDATE.value,
        "evidence_sufficiency": "sufficient",
        "insufficient_evidence": False,
        "claim_allowed": False,
        "required_future_artifacts": required,
        "warning": "claim_still_disabled_until_registered_full_evidence",
    }

