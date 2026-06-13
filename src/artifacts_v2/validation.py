from __future__ import annotations

from pathlib import Path
from typing import Any

from .hashing import sha256_file
from .registry import read_registry
from .schema import ARTIFACT_TYPES


class ArtifactRegistryError(ValueError):
    pass


REQUIRED_FIELDS = [
    "artifact_id",
    "artifact_type",
    "path",
    "hash",
    "created_at",
    "step",
    "scope",
    "dataset_name",
    "method_name",
    "model_name",
    "tokenizer_name",
    "evidence_level",
    "smoke_only",
    "protocol_only",
    "completed",
    "main_evidence",
    "level3_evidence",
    "parent_artifacts",
    "derived_artifacts",
    "claim_ids",
    "notes",
]


def validate_registry_rows(rows: list[dict[str, Any]], root: Path) -> list[str]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=1):
        missing = [field for field in REQUIRED_FIELDS if field not in row]
        if missing:
            errors.append(f"row {index} missing fields: {', '.join(missing)}")
            continue
        if row["artifact_type"] not in ARTIFACT_TYPES:
            errors.append(f"row {index} unsupported artifact_type: {row['artifact_type']}")
        path = root / str(row["path"])
        if not path.exists():
            errors.append(f"row {index} path missing: {row['path']}")
            continue
        actual = sha256_file(path)
        if actual != row["hash"]:
            errors.append(f"row {index} hash mismatch: {row['path']}")
        if row.get("smoke_only") is True and row.get("main_evidence") is True:
            errors.append(f"row {index} smoke artifact marked main_evidence: {row['path']}")
        if row.get("protocol_only") is True and row.get("completed") is True:
            errors.append(f"row {index} protocol artifact marked completed: {row['path']}")
        if row.get("level3_evidence") is True and row.get("evidence_level") != "level3_completed":
            errors.append(f"row {index} level3_evidence without level3_completed evidence: {row['path']}")
    return errors


def validate_registry_file(path: Path, root: Path) -> list[str]:
    return validate_registry_rows(read_registry(path), root)

