from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashing import sha256_file
from .schema import ArtifactRecord


def _rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _normalize_repo_relative_path(path: Path, repo_root: Path) -> str:
    """Return a repo-relative POSIX path before path-pattern classification."""
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _artifact_type(path: Path) -> str:
    name = path.name
    if name == "dataset_manifest.json":
        return "dataset_manifest"
    if name == "data_manifest.json":
        return "dataset_manifest"
    if name == "tokenizer_manifest.json":
        return "tokenizer_manifest"
    if name == "filter_manifest.json":
        return "filter_manifest"
    if name == "training_manifest.json":
        return "training_manifest"
    if name == "checkpoint_manifest.json":
        return "checkpoint_manifest"
    if name == "evaluation_manifest.json":
        return "evaluation_manifest"
    if name == "mechanism_manifest.json":
        return "mechanism_manifest"
    if name.endswith("_readiness_report.json") or name in {"level3_gates_report.json"}:
        return "readiness_report"
    if name.endswith("_report.json"):
        return "report"
    if "claim_map" in path.as_posix() and path.suffix == ".json":
        return "claim_map"
    if name in {"main_results.csv", "cross_dataset_results.csv"}:
        return "main_table"
    if "artifacts/localmax_tables/" in path.as_posix() and path.suffix.casefold() == ".csv":
        return "report"
    if "artifacts/level3_tables/" in path.as_posix() and path.suffix.casefold() == ".csv":
        return "level3_main_result"
    if path.suffix.casefold() in {".png", ".jpg", ".jpeg", ".svg"}:
        return "figure"
    if path.suffix.casefold() in {".md", ".txt"}:
        return "report"
    return "smoke_output" if "smoke" in path.as_posix().casefold() else "protocol_output"


def _step_from_path(rel_path: str) -> str:
    text = rel_path.casefold()
    for token in ["step10b", "step10a", "step10", "step9", "step8", "step7", "step6", "step5", "step4", "step3", "step2", "step1", "step0"]:
        if token in text:
            if token == "step10b":
                return "step10B"
            return "step10A" if token == "step10a" else token
    if "main_results" in text:
        return "historical"
    if "localmax" in text:
        return "step10B_localmax"
    return "unknown"


def _evidence_level(path: Path, payload: dict[str, Any], artifact_type: str) -> str:
    if artifact_type == "main_table":
        return "historical_main_only"
    if payload.get("level3_evidence") is True:
        return "level3_completed"
    if payload.get("smoke_only") is True or "smoke" in path.as_posix().casefold():
        return "smoke_only"
    if payload.get("protocol_only") is True or "protocol" in path.as_posix().casefold():
        return "protocol_only"
    if artifact_type == "readiness_report":
        return "pipeline_hygiene"
    return "sample_partial"


def _record_for(path: Path, root: Path) -> ArtifactRecord:
    payload = _load_json(path) if path.suffix == ".json" else {}
    rel = _normalize_repo_relative_path(path, root)
    artifact_type = _artifact_type(path)
    evidence_level = _evidence_level(path, payload, artifact_type)
    smoke_only = bool(payload.get("smoke_only", evidence_level == "smoke_only"))
    protocol_only = bool(payload.get("protocol_only", evidence_level == "protocol_only"))
    completed = bool(payload.get("completed", artifact_type == "main_table"))
    main_evidence = artifact_type == "main_table" and "analysis_step" not in rel and "training_step5" not in rel
    level3_evidence = bool(payload.get("level3_evidence", False))
    dataset_name = str(payload.get("dataset_name", ""))
    method_name = str(
        payload.get("method_name")
        or payload.get("filter_name")
        or payload.get("analysis_name")
        or payload.get("evaluation_name")
        or ""
    )
    model_name = str(payload.get("model_config", {}).get("model_name", "") if isinstance(payload.get("model_config"), dict) else "")
    tokenizer_name = str(payload.get("tokenizer_name") or payload.get("tokenizer_type") or "")
    parents = []
    for field in [
        "dataset_manifest_path",
        "tokenizer_manifest_path",
        "filter_manifest_path",
        "training_manifest_path",
        "evaluation_manifest_path",
        "input_manifest_paths",
        "filter_manifest_paths",
        "evaluation_manifest_paths",
    ]:
        value = payload.get(field)
        if isinstance(value, str) and value:
            parents.append(value)
        elif isinstance(value, list):
            parents.extend([str(item) for item in value if str(item)])
    return ArtifactRecord(
        artifact_id=rel.replace("/", "::"),
        artifact_type=artifact_type,
        path=rel,
        hash=sha256_file(path),
        created_at=str(payload.get("created_at") or datetime.now(timezone.utc).replace(microsecond=0).isoformat()),
        step=_step_from_path(rel),
        scope=str(payload.get("scope", "historical" if artifact_type == "main_table" else "")),
        dataset_name=dataset_name,
        method_name=method_name,
        model_name=model_name,
        tokenizer_name=tokenizer_name,
        evidence_level=evidence_level,
        smoke_only=smoke_only,
        protocol_only=protocol_only,
        completed=completed,
        main_evidence=main_evidence,
        level3_evidence=level3_evidence,
        parent_artifacts=sorted(set(parents)),
        derived_artifacts=[],
        claim_ids=[],
        notes="historical_legacy=true" if artifact_type == "main_table" else "registry_v2_scanned",
    )


def scan_artifacts(root: Path) -> list[ArtifactRecord]:
    patterns = [
        "artifacts/**/data_manifest.json",
        "artifacts/**/dataset_manifest.json",
        "artifacts/**/tokenizer_manifest.json",
        "artifacts/**/filter_manifest.json",
        "artifacts/**/training_manifest.json",
        "artifacts/**/checkpoint_manifest.json",
        "artifacts/**/evaluation_manifest.json",
        "artifacts/**/mechanism_manifest.json",
        "artifacts/reports/*readiness_report.json",
        "artifacts/reports/step10B_*_report.json",
        "artifacts/reports/localmax_*_report.json",
        "artifacts/claim_map/*.json",
        "artifacts/level3_tables/*",
        "artifacts/level3_reports/*",
        "artifacts/localmax_tables/*",
        "artifacts/localmax_reports/*",
        "artifacts/localmax_filters/*_status.json",
        "artifacts/localmax_training/*_status.json",
        "artifacts/localmax_evaluation/*_status.json",
        "artifacts/localmax_mechanisms/*_status.json",
        "artifacts/localmax_analysis/*",
        "artifacts/localmax_training_strengthened/**/training_manifest.json",
        "artifacts/localmax_training_strengthened/**/checkpoint_manifest.json",
        "artifacts/localmax_evaluation_strengthened/*",
        "artifacts/localmax_analysis_strengthened/*",
        "artifacts/localmax_release/**/*",
        "artifacts/tables/main_results.csv",
        "artifacts/stats/main_results.csv",
        "artifacts/cross_dataset/cross_dataset_results.csv",
        "artifacts/figures/*",
        "docs/*.md",
    ]
    records: dict[str, ArtifactRecord] = {}
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if path.is_file():
                record = _record_for(path, root)
                records[record.path] = record
    return list(records.values())
