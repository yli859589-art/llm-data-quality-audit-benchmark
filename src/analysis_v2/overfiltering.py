from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import MechanismAnalysisConfig, MechanismAnalysisResult
from .evidence import assess_evidence
from .io import read_json, resolve_path, write_csv, write_json, write_text
from .manifest import create_mechanism_manifest, sha256_file, write_manifest
from .reporting import mechanism_report


def _output_path(manifest: dict[str, Any], name: str, root: Path) -> Path:
    return resolve_path(str(manifest["output_hashes"][name]["path"]), root)


def run_overfiltering_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    filter_manifest = read_json(config.filter_manifest_paths[0], root)
    keep_report = read_json(_output_path(filter_manifest, "keep_rate_report.json", root))
    risk_report = read_json(_output_path(filter_manifest, "risk_report.json", root))
    diversity_report = read_json(_output_path(filter_manifest, "diversity_report.json", root))
    cost_report = read_json(_output_path(filter_manifest, "cost_report.json", root))
    sample_size = int(filter_manifest.get("input_docs", 0) or 0)
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=sample_size,
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=["matched utility metrics", "larger sample", "multi-baseline keep-rate matrix"],
    )
    row = {
        "method_name": config.methods[0] if config.methods else filter_manifest.get("filter_name", ""),
        "document_keep_rate": keep_report.get("document_keep_rate"),
        "token_keep_rate": keep_report.get("token_keep_rate"),
        "input_docs": keep_report.get("input_docs"),
        "kept_docs": keep_report.get("kept_docs"),
        "input_tokens": keep_report.get("input_estimated_tokens", filter_manifest.get("input_estimated_tokens")),
        "kept_tokens": keep_report.get("kept_estimated_tokens", filter_manifest.get("kept_estimated_tokens")),
        "risk_delta_proxy": "unavailable_no_raw_pair",
        "diversity_delta_proxy": "unavailable_no_raw_pair",
        "cost_delta_proxy": cost_report.get("filter_runtime_seconds"),
        "risk_proxy_snapshot": risk_report.get("symbol_ratio"),
        "diversity_proxy_snapshot": diversity_report.get("lexical_diversity"),
        "overfiltering_warning": "potential_smoke_only_overfiltering_diagnostic" if sample_size < 30 else "none",
        "insufficient_evidence": True,
        "notes": "Smoke-only keep-rate diagnostic; not a formal overfiltering conclusion.",
    }
    summary = {
        "sample_size": sample_size,
        "document_keep_rate": row["document_keep_rate"],
        "token_keep_rate": row["token_keep_rate"],
        "overfiltering_warning": row["overfiltering_warning"],
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "overfiltering_diagnostics.csv"
    summary_path = output_dir / "overfiltering_summary.json"
    report_path = output_dir / "overfiltering_report.md"
    write_csv(table_path, [row])
    write_json(summary_path, summary)
    write_text(
        report_path,
        mechanism_report(
            "Overfiltering Analysis",
            summary,
            "This report checks keep-rate and token-retention diagnostics. It only flags potential smoke risks.",
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
        notes="Overfiltering smoke diagnostic only.",
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
        "Potential overfiltering diagnostic only.",
    )

