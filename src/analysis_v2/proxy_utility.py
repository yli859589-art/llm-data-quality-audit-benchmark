from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import MechanismAnalysisConfig, MechanismAnalysisResult
from .evidence import assess_evidence
from .io import read_json, read_jsonl, resolve_path, write_csv, write_json, write_text
from .manifest import create_mechanism_manifest, sha256_file, write_manifest
from .reporting import mechanism_report


def _output_path(manifest: dict[str, Any], name: str, root: Path) -> Path:
    return resolve_path(str(manifest["output_hashes"][name]["path"]), root)


def _lm_smoke_metric(config: MechanismAnalysisConfig, root: Path) -> Any:
    if not config.evaluation_manifest_paths:
        return None
    manifest = read_json(config.evaluation_manifest_paths[0], root)
    metrics_path = manifest.get("metrics_path")
    if not metrics_path:
        return None
    metrics = read_json(str(metrics_path), root)
    return metrics.get("validation_loss") or metrics.get("budget_normalized_ppl_diagnostic")


def run_proxy_utility_analysis(
    config: MechanismAnalysisConfig, output_dir: Path, root: Path
) -> MechanismAnalysisResult:
    filter_manifest = read_json(config.filter_manifest_paths[0], root)
    component_rows = read_jsonl(_output_path(filter_manifest, "component_scores.jsonl", root))
    lm_metric = _lm_smoke_metric(config, root)
    evidence = assess_evidence(
        scope=config.scope,
        sample_size=len(component_rows),
        smoke_only=config.smoke_only,
        protocol_only=config.protocol_only,
        required_future_artifacts=[
            "per-document utility target",
            "registered multi-seed LM metrics",
            "matched raw/random/dedup/URD comparisons",
        ],
    )
    rows = []
    for row in component_rows:
        rows.append(
            {
                "method_name": config.methods[0] if config.methods else filter_manifest.get("filter_name", ""),
                "doc_id": row.get("doc_id", ""),
                "utility_score": row.get("utility_score", ""),
                "risk_score": row.get("risk_score", ""),
                "diversity_score": row.get("diversity_score", ""),
                "filter_score": row.get("urd_score", ""),
                "lm_smoke_metric": lm_metric,
                "correlation_diagnostic": "unavailable_no_per_document_utility_target",
                "sample_size": len(component_rows),
                "insufficient_evidence": True,
                "notes": "Smoke diagnostic hook only; no full-scale proxy-utility mismatch conclusion.",
            }
        )
    summary = {
        "analysis_type": config.analysis_type,
        "sample_size": len(component_rows),
        "lm_smoke_metric_available": lm_metric is not None,
        "per_document_utility_target_available": False,
        "evidence_sufficiency": evidence["evidence_sufficiency"],
        "insufficient_evidence": evidence["insufficient_evidence"],
        "claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    table_path = output_dir / "proxy_utility_diagnostics.csv"
    summary_path = output_dir / "proxy_utility_summary.json"
    report_path = output_dir / "proxy_utility_report.md"
    write_csv(table_path, rows)
    write_json(summary_path, summary)
    write_text(
        report_path,
        mechanism_report(
            "Proxy-Utility Mismatch Analysis",
            summary,
            "The analyzer links URD/filter component scores to available smoke LM diagnostics. "
            "Because no per-document utility target exists, it explicitly reports insufficient evidence.",
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
        insufficient_evidence=bool(evidence["insufficient_evidence"]),
        completed=True,
        notes="Proxy-utility smoke diagnostic only.",
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
        "Diagnostic hook implemented; no full-scale mismatch claim.",
    )

