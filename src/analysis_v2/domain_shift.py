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


def run_domain_shift_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    filter_manifest = read_json(config.filter_manifest_paths[0], root)
    component_rows = read_jsonl(_output_path(filter_manifest, "component_scores.jsonl", root))
    length_shift = []
    vocab_shift = []
    source_shift = []
    for row in component_rows:
        shift = row.get("shift_components", {})
        length_shift.append(float(shift.get("length_distribution_shift_proxy", 0.0) or 0.0))
        vocab_shift.append(float(shift.get("vocabulary_distribution_shift_proxy", 0.0) or 0.0))
        source_shift.append(float(shift.get("source_domain_distribution_shift_proxy", 0.0) or 0.0))
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=len(component_rows),
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=["selected-vs-input full split comparison", "domain metadata", "token distribution audit"],
    )
    row = {
        "method_name": config.methods[0] if config.methods else filter_manifest.get("filter_name", ""),
        "length_shift_proxy": mean_or_none(length_shift),
        "token_distribution_shift_proxy": mean_or_none(vocab_shift),
        "vocab_coverage_shift_proxy": mean_or_none(vocab_shift),
        "source_shift_proxy": mean_or_none(source_shift),
        "source_domain_shift_unavailable": True,
        "distribution_shift_warning": "smoke_sample_too_small_for_shift_conclusion",
        "insufficient_evidence": True,
        "notes": "Input-relative shift proxy only; no formal domain-shift conclusion.",
    }
    summary = {
        "sample_size": len(component_rows),
        "length_shift_proxy": row["length_shift_proxy"],
        "token_distribution_shift_proxy": row["token_distribution_shift_proxy"],
        "source_domain_shift_unavailable": True,
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "domain_shift_diagnostics.csv"
    summary_path = output_dir / "domain_shift_summary.json"
    report_path = output_dir / "domain_shift_report.md"
    write_csv(table_path, [row])
    write_json(summary_path, summary)
    write_text(
        report_path,
        mechanism_report(
            "Domain and Distribution Shift Analysis",
            summary,
            "The report surfaces length/token proxy shifts and marks domain metadata as unavailable.",
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
        notes="Domain-shift smoke diagnostic only.",
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
        "Distribution-shift diagnostic only.",
    )

