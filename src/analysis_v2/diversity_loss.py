from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import MechanismAnalysisConfig, MechanismAnalysisResult
from .evidence import assess_evidence
from .io import mean_or_none, read_json, read_jsonl, resolve_path, write_csv, write_json, write_text
from .manifest import create_mechanism_manifest, sha256_file, write_manifest
from .reporting import mechanism_report


def _output_path(manifest: dict[str, Any], name: str, root: Path) -> Path:
    return resolve_path(str(manifest["output_hashes"][name]["path"]), root)


def run_diversity_loss_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    filter_manifest = read_json(config.filter_manifest_paths[0], root)
    diversity_report = read_json(_output_path(filter_manifest, "diversity_report.json", root))
    component_rows = read_jsonl(_output_path(filter_manifest, "component_scores.jsonl", root))
    diversity_scores = [float(row.get("diversity_score", 0.0) or 0.0) for row in component_rows]
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=len(component_rows),
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=["raw-vs-selected diversity pair", "source/domain metadata", "semantic embedding diversity"],
    )
    row = {
        "method_name": config.methods[0] if config.methods else filter_manifest.get("filter_name", ""),
        "unique_token_ratio": diversity_report.get("unique_token_ratio"),
        "lexical_diversity": diversity_report.get("lexical_diversity"),
        "entropy": "proxy_available_in_component_scores",
        "source_count": diversity_report.get("source_count"),
        "coverage_proxy": "hash_vector_and_cluster_proxy",
        "diversity_score_mean": mean_or_none(diversity_scores),
        "source_domain_unavailable": diversity_report.get("source_count", 0) <= 1,
        "semantic_embedding_unavailable": True,
        "diversity_loss_warning": "source_or_semantic_evidence_unavailable",
        "insufficient_evidence": True,
        "notes": "Proxy diversity diagnostic only; no semantic diversity conclusion.",
    }
    summary = {
        "sample_size": len(component_rows),
        "diversity_score_mean": row["diversity_score_mean"],
        "source_domain_unavailable": row["source_domain_unavailable"],
        "semantic_embedding_unavailable": True,
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "diversity_loss_diagnostics.csv"
    summary_path = output_dir / "diversity_loss_summary.json"
    report_path = output_dir / "diversity_loss_report.md"
    write_csv(table_path, [row])
    write_json(summary_path, summary)
    write_text(
        report_path,
        mechanism_report(
            "Diversity Loss Analysis",
            summary,
            "The report exposes lexical/hash diversity proxies and marks source-domain and semantic coverage gaps.",
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
        notes="Diversity-loss smoke diagnostic only.",
    )
    write_manifest(output_dir / "mechanism_manifest.json", manifest)
    return MechanismAnalysisResult(
        config.analysis_name,
        config.analysis_type,
        config.scope,
        config.dataset_name,
        config.methods,
        summary,
        [row],
        str(evidence["evidence_sufficiency"]),
        {config.filter_manifest_paths[0]: sha256_file(resolve_path(config.filter_manifest_paths[0], root))},
        {"table": table_path.as_posix(), "report": report_path.as_posix(), "summary": summary_path.as_posix()},
        config.smoke_only,
        config.protocol_only,
        True,
        False,
        "Proxy diversity diagnostic only.",
    )

