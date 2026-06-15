from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import MechanismAnalysisConfig
from .io import project_relative, resolve_path
from .schema import MANIFEST_VERSION


def _canonical_file_bytes(path: str | Path) -> bytes:
    data = Path(path).read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n")
    return normalized.encode("utf-8")


def sha256_file(path: str | Path) -> str:
    return hashlib.sha256(_canonical_file_bytes(path)).hexdigest()


def sha256_file_variants(path: str | Path) -> set[str]:
    data = Path(path).read_bytes()
    variants = {hashlib.sha256(data).hexdigest()}
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return variants
    normalized_lf = text.replace("\r\n", "\n").replace("\r", "\n")
    variants.add(hashlib.sha256(normalized_lf.encode("utf-8")).hexdigest())
    variants.add(hashlib.sha256(normalized_lf.replace("\n", "\r\n").encode("utf-8")).hexdigest())
    return variants


def _existing_relative_paths(paths: list[str], root: Path) -> list[str]:
    result = []
    for path in paths:
        resolved = resolve_path(path, root)
        if resolved.exists():
            result.append(project_relative(resolved, root))
    return result


def _hash_paths(paths: list[str], root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in paths:
        resolved = resolve_path(path, root)
        if resolved.exists():
            hashes[project_relative(resolved, root)] = sha256_file(resolved)
    return hashes


def create_mechanism_manifest(
    *,
    config: MechanismAnalysisConfig,
    root: Path,
    diagnostic_table_path: Path,
    diagnostic_report_path: Path,
    figure_paths: list[Path] | None,
    extra_output_paths: list[Path] | None,
    evidence_sufficiency: str,
    insufficient_evidence: bool,
    completed: bool,
    notes: str,
) -> dict[str, Any]:
    figures = figure_paths or []
    extras = extra_output_paths or []
    return {
        "manifest_version": MANIFEST_VERSION,
        "analysis_name": config.analysis_name,
        "analysis_type": config.analysis_type,
        "scope": config.scope,
        "smoke_only": bool(config.smoke_only),
        "protocol_only": bool(config.protocol_only),
        "completed": bool(completed),
        "dataset_name": config.dataset_name,
        "methods": list(config.methods),
        "input_artifact_paths": _existing_relative_paths(config.input_artifact_paths, root),
        "input_artifact_hashes": _hash_paths(config.input_artifact_paths, root),
        "input_manifest_paths": _existing_relative_paths(config.input_manifest_paths, root),
        "input_manifest_hashes": _hash_paths(config.input_manifest_paths, root),
        "training_manifest_paths": _existing_relative_paths(config.training_manifest_paths, root),
        "training_manifest_hashes": _hash_paths(config.training_manifest_paths, root),
        "filter_manifest_paths": _existing_relative_paths(config.filter_manifest_paths, root),
        "filter_manifest_hashes": _hash_paths(config.filter_manifest_paths, root),
        "evaluation_manifest_paths": _existing_relative_paths(config.evaluation_manifest_paths, root),
        "evaluation_manifest_hashes": _hash_paths(config.evaluation_manifest_paths, root),
        "tokenizer_manifest_paths": _existing_relative_paths(config.tokenizer_manifest_paths, root),
        "tokenizer_manifest_hashes": _hash_paths(config.tokenizer_manifest_paths, root),
        "diagnostic_table_path": project_relative(diagnostic_table_path, root),
        "diagnostic_table_hash": sha256_file(diagnostic_table_path),
        "diagnostic_report_path": project_relative(diagnostic_report_path, root),
        "diagnostic_report_hash": sha256_file(diagnostic_report_path),
        "figure_paths": [project_relative(path, root) for path in figures],
        "figure_hashes": {project_relative(path, root): sha256_file(path) for path in figures},
        "extra_output_paths": [project_relative(path, root) for path in extras],
        "extra_output_hashes": {project_relative(path, root): sha256_file(path) for path in extras},
        "evidence_sufficiency": evidence_sufficiency,
        "insufficient_evidence": bool(insufficient_evidence),
        "claim_allowed": False,
        "effectiveness_claim_allowed": False,
        "full_scale_mechanism_conclusion_allowed": False,
        "main_results_modified": False,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "notes": notes,
    }


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
