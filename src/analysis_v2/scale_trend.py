from __future__ import annotations

from pathlib import Path

from .base import MechanismAnalysisConfig, MechanismAnalysisResult
from .evidence import assess_evidence
from .io import write_csv, write_json, write_text
from .manifest import create_mechanism_manifest, write_manifest
from .reporting import mechanism_report


def run_scale_trend_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    tiny_smoke = root / "artifacts" / "training_step5" / "wikitext2_smoke_bpe_tiny" / "training_manifest.json"
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=0,
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=["small BPE runs", "medium runs", "large-lite runs", "multi-seed scale matrix"],
    )
    rows = [
        {
            "scale": "tiny_smoke",
            "status": "available" if tiny_smoke.exists() else "unavailable",
            "main_evidence": False,
            "notes": "Smoke engineering run only.",
        },
        {"scale": "small", "status": "future_required", "main_evidence": False, "notes": "Formal BPE evidence not completed."},
        {"scale": "medium", "status": "future_required", "main_evidence": False, "notes": "Protocol only."},
        {"scale": "large_lite", "status": "future_required", "main_evidence": False, "notes": "Protocol only."},
    ]
    summary = {
        "scale_trend_completed": False,
        "tiny_smoke_available": tiny_smoke.exists(),
        "medium_or_large_lite_completed": False,
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "scale_trend_diagnostics.csv"
    summary_path = output_dir / "scale_trend_summary.json"
    report_path = output_dir / "scale_trend_report.md"
    write_csv(table_path, rows)
    write_json(summary_path, summary)
    write_text(
        report_path,
        mechanism_report(
            "Scale Trend Protocol",
            summary,
            "This protocol records which model scales are future requirements. It does not report a completed trend.",
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
        notes="Scale trend protocol only.",
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
        {},
        {"table": table_path.as_posix(), "report": report_path.as_posix(), "summary": summary_path.as_posix()},
        config.smoke_only,
        config.protocol_only,
        True,
        False,
        "Protocol-only scale-trend plan.",
    )

