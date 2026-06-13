from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import MechanismAnalysisConfig, MechanismAnalysisResult
from .evidence import assess_evidence
from .io import read_csv, read_json, read_jsonl, resolve_path, write_csv, write_json, write_text
from .manifest import create_mechanism_manifest, sha256_file, write_manifest
from .reporting import mechanism_report


def _output_path(manifest: dict[str, Any], name: str, root: Path) -> Path:
    return resolve_path(str(manifest["output_hashes"][name]["path"]), root)


def run_pareto_mechanism_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    filter_manifest = read_json(config.filter_manifest_paths[0], root)
    component_rows = read_jsonl(_output_path(filter_manifest, "component_scores.jsonl", root))
    frontier_rows = read_csv(_output_path(filter_manifest, "pareto_frontier.csv", root))
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=len(frontier_rows),
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=["multi-method Pareto comparison", "utility/risk/diversity/cost completed metrics"],
    )
    rows = [
        {
            "method_name": config.methods[0] if config.methods else filter_manifest.get("filter_name", ""),
            "doc_id": row.get("doc_id", ""),
            "pareto_rank": row.get("pareto_rank", ""),
            "selected": row.get("selected", ""),
            "utility_score": row.get("utility_score", ""),
            "risk_score": row.get("risk_score", ""),
            "diversity_score": row.get("diversity_score", ""),
            "cost_score": row.get("cost_score", ""),
            "pareto_improvement_claim_allowed": False,
            "insufficient_evidence": True,
            "notes": "Smoke Pareto diagnostic; no frontier-improvement claim.",
        }
        for row in frontier_rows
    ]
    selected_count = len([row for row in frontier_rows if str(row.get("selected", "")).casefold() == "true"])
    summary = {
        "frontier_rows": len(frontier_rows),
        "component_score_rows": len(component_rows),
        "selected_rows": selected_count,
        "multi_method_full_comparison_available": False,
        "pareto_improvement_claim_allowed": False,
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "pareto_mechanism_diagnostics.csv"
    summary_path = output_dir / "pareto_mechanism_summary.json"
    report_path = output_dir / "pareto_mechanism_report.md"
    write_csv(table_path, rows)
    write_json(summary_path, summary)
    write_text(
        report_path,
        mechanism_report(
            "Pareto Mechanism Analysis",
            summary,
            "The analyzer reads Step 6/7 Pareto artifacts as smoke diagnostics only. It does not claim frontier improvement.",
        ),
    )
    manifest = create_mechanism_manifest(
        config=config,
        root=root,
        diagnostic_table_path=table_path,
        diagnostic_report_path=report_path,
        figure_paths=[],
        extra_output_paths=[summary_path],
        evidence_sufficiency=str(evidence["evidence_sufficiency"]),
        insufficient_evidence=True,
        completed=True,
        notes="Pareto mechanism smoke diagnostic only.",
    )
    write_manifest(output_dir / "mechanism_manifest.json", manifest)
    return MechanismAnalysisResult(
        config.analysis_name,
        config.analysis_type,
        config.scope,
        config.dataset_name,
        config.methods,
        summary,
        rows,
        str(evidence["evidence_sufficiency"]),
        {config.filter_manifest_paths[0]: sha256_file(resolve_path(config.filter_manifest_paths[0], root))},
        {"table": table_path.as_posix(), "report": report_path.as_posix(), "summary": summary_path.as_posix()},
        config.smoke_only,
        config.protocol_only,
        True,
        False,
        "Pareto mechanism diagnostic only.",
    )

