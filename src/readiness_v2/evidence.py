from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceRequirement:
    name: str
    required: bool
    present: bool
    notes: str


def status_from_requirements(requirements: list[EvidenceRequirement]) -> str:
    if not requirements:
        return "not_ready"
    required = [item for item in requirements if item.required]
    if required and all(item.present for item in required):
        return "pass"
    if any(item.present for item in requirements):
        return "partial"
    return "not_ready"

