from __future__ import annotations

from pathlib import Path

from .base import MechanismAnalysisConfig, MechanismAnalysisResult
from .evidence import assess_evidence
from .io import write_csv, write_json, write_text
from .manifest import create_mechanism_manifest, write_manifest
from .reporting import mechanism_report


def run_rank_stability_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=0,
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=["multi-seed runs", "method-level metric matrix", "bootstrap rank uncertainty table"],
    )
    row = {
        "method_name": config.methods[0] if config.methods else "protocol_only",
        "methods_available": len(config.methods),
        "seeds_available": 0,
        "bootstrap_rank_uncertainty": "future_required",
        "rank_correlation": "unavailable",
        "ranking_stability_status": "insufficient_evidence",
        "insufficient_evidence": True,
        "notes": "Protocol-only rank stability plan; no stability claim.",
    }
    summary = {
        "rank_stability_completed": False,
        "multi_seed_evidence_available": False,
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "rank_stability_diagnostics.csv"
    summary_path = output_dir / "rank_stability_summary.json"
    report_path = output_dir / "rank_stability_report.md"
    write_csv(table_path, [row])
    write_json(summary_path, summary)
    write_text(
        report_path,
        mechanism_report(
            "Rank Stability Protocol",
            summary,
            "This is a protocol-only artifact. Current evidence is insufficient for ranking-stability claims.",
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
        completed=False,
        notes="Rank stability protocol only.",
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
        {},
        {"table": table_path.as_posix(), "report": report_path.as_posix(), "summary": summary_path.as_posix()},
        config.smoke_only,
        config.protocol_only,
        True,
        False,
        "Protocol-only rank-stability plan.",
    )

