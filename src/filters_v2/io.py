from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .base import BaseFilter, FilterInput, FilterResult
from .cost import build_cost_report
from .diversity import build_diversity_report
from .keep_rate import validate_keep_rate
from .manifest import create_filter_manifest, sha256_file
from .risk import build_risk_report


def project_relative(path: str | Path, root: Path) -> str:
    value = Path(path)
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return value.as_posix()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + ("\n" if rows else ""),
        encoding="utf-8",
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_filter_inputs(path: str | Path) -> list[FilterInput]:
    rows: list[FilterInput] = []
    for index, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            continue
        rows.append(FilterInput.from_mapping(json.loads(line), index=index))
    return rows


def output_hashes_for(output_dir: Path, root: Path) -> dict[str, dict[str, str]]:
    output_names = [
        "selected_doc_ids.jsonl",
        "decisions.jsonl",
        "scores.jsonl",
        "keep_rate_report.json",
        "risk_report.json",
        "diversity_report.json",
        "cost_report.json",
    ]
    return {
        name: {
            "path": project_relative(output_dir / name, root),
            "sha256": sha256_file(output_dir / name),
        }
        for name in output_names
    }


def write_filter_outputs(
    *,
    filter_instance: BaseFilter,
    result: FilterResult,
    records: list[FilterInput],
    output_dir: Path,
    root: Path,
    runtime_seconds: float,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    decision_rows = [decision.to_dict() for decision in result.decisions]
    selected_rows = [
        {
            "doc_id": decision.doc_id,
            "keep": decision.keep,
            "score": decision.score,
            "reason": decision.reason,
        }
        for decision in result.decisions
    ]
    score_rows = [
        {
            "doc_id": decision.doc_id,
            "score": decision.score,
            "component_scores": decision.metadata.get("component_scores", {}),
            "metadata": decision.metadata,
        }
        for decision in result.decisions
    ]
    kept_ids = {decision.doc_id for decision in result.decisions if decision.keep}
    kept_records = [record for record in records if record.doc_id in kept_ids]
    keep_rate_report = {
        "status": "passed",
        "filter_name": result.filter_name,
        "filter_type": result.filter_type,
        "input_docs": result.input_docs,
        "kept_docs": result.kept_docs,
        "input_estimated_tokens": result.input_estimated_tokens,
        "kept_estimated_tokens": result.kept_estimated_tokens,
        "document_keep_rate": result.document_keep_rate,
        "token_keep_rate": result.token_keep_rate,
        "target_keep_rate": filter_instance.config.target_keep_rate,
        "target_keep_rate_check": validate_keep_rate(
            result.document_keep_rate,
            filter_instance.config.target_keep_rate,
        ),
        "token_counter_type": filter_instance.config.token_counter_type,
        "notes": "Document keep-rate and token keep-rate are both reported for later fairness checks.",
    }
    risk_report = build_risk_report(records, kept_records)
    diversity_report = build_diversity_report(kept_records)
    cost_report = build_cost_report(
        runtime_seconds=runtime_seconds,
        input_docs=result.input_docs,
        kept_docs=result.kept_docs,
        external_dependency_used=filter_instance.external_dependency_available,
    )
    write_jsonl(output_dir / "selected_doc_ids.jsonl", selected_rows)
    write_jsonl(output_dir / "decisions.jsonl", decision_rows)
    write_jsonl(output_dir / "scores.jsonl", score_rows)
    write_json(output_dir / "keep_rate_report.json", keep_rate_report)
    write_json(output_dir / "risk_report.json", risk_report)
    write_json(output_dir / "diversity_report.json", diversity_report)
    write_json(output_dir / "cost_report.json", cost_report)
    hashes = output_hashes_for(output_dir, root)
    manifest = create_filter_manifest(
        config=filter_instance.config,
        result=result,
        root=root,
        output_dir=output_dir,
        output_hashes=hashes,
        proxy_used=filter_instance.proxy_used,
        external_dependency=filter_instance.external_dependency,
        external_dependency_available=filter_instance.external_dependency_available,
        implemented_but_not_run=filter_instance.implemented_but_not_run,
        historical_baseline=filter_instance.historical_baseline,
        official_reproduction=filter_instance.official_reproduction,
        notes=result.summary.get("notes", ""),
    )
    write_json(output_dir / "filter_manifest.json", manifest)
    return manifest
