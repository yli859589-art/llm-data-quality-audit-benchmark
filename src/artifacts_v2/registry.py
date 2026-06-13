from __future__ import annotations

from collections import Counter
from pathlib import Path

import json

from .canonical_io import write_canonical_json, write_canonical_jsonl
from .scanner import scan_artifacts
from .schema import ArtifactRecord


def write_registry(root: Path) -> tuple[Path, Path, list[ArtifactRecord]]:
    records = scan_artifacts(root)
    output_dir = root / "artifacts" / "registry_v2"
    output_dir.mkdir(parents=True, exist_ok=True)
    registry_path = output_dir / "artifact_registry.jsonl"
    summary_path = output_dir / "artifact_registry_summary.json"
    write_canonical_jsonl(
        registry_path,
        [record.to_dict() for record in sorted(records, key=lambda item: item.path)],
    )
    type_counts = Counter(record.artifact_type for record in records)
    evidence_counts = Counter(record.evidence_level for record in records)
    summary = {
        "record_count": len(records),
        "artifact_type_counts": dict(sorted(type_counts.items())),
        "evidence_level_counts": dict(sorted(evidence_counts.items())),
        "main_evidence_records": len([record for record in records if record.main_evidence]),
        "level3_evidence_records": len([record for record in records if record.level3_evidence]),
        "warnings": [
            "Legacy main tables are marked historical_legacy=true rather than reconstructed with fake lineage.",
            "Smoke/protocol artifacts are registered but not treated as main evidence.",
        ],
    }
    write_canonical_json(summary_path, summary)
    return registry_path, summary_path, records


def read_registry(path: Path) -> list[dict]:
    rows = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
