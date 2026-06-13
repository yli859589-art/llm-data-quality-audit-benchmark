from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import EvaluationConfig, EvaluationResult
from .io import read_json, read_jsonl, resolve_path, write_csv, write_json, write_text
from .manifest import create_evaluation_manifest, sha256_file, write_manifest
from .reporting import simple_report
from .statistics import summary_stats


def _output_path(manifest: dict[str, Any], name: str, root: Path) -> Path:
    return resolve_path(str(manifest["output_hashes"][name]["path"]), root)


def run_risk_evaluation(config: EvaluationConfig, output_dir: Path, root: Path) -> EvaluationResult:
    filter_manifest = read_json(config.filter_manifest_path, root)
    risk_report = read_json(_output_path(filter_manifest, "risk_report.json", root))
    component_rows = read_jsonl(_output_path(filter_manifest, "component_scores.jsonl", root))
    risk_scores = [float(row.get("risk_score", 0.0) or 0.0) for row in component_rows]
    stats = summary_stats(risk_scores)
    metrics = {
        "url_ratio": risk_report.get("url_ratio", 0),
        "html_ratio": risk_report.get("html_ratio", 0),
        "symbol_ratio": risk_report.get("symbol_ratio", 0),
        "digit_ratio": risk_report.get("digit_ratio", 0),
        "repetition_ratio": risk_report.get("repetition_ratio", 0),
        "estimated_pii_hits": risk_report.get("estimated_pii_hits", 0),
        "boilerplate_ratio": "proxy_available_in_component_scores",
        "risk_score_mean": stats["mean"],
        "risk_score_std": stats["std"],
        "toxicity_classifier": "unavailable",
        "proxy_metric": True,
        "main_evidence": False,
        "effectiveness_claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "risk_metrics.json"
    summary_path = output_dir / "risk_summary.csv"
    report_path = output_dir / "risk_evaluation_report.md"
    write_json(metrics_path, metrics)
    write_csv(summary_path, [{"method_name": config.method_name, **metrics}], list({"method_name": config.method_name, **metrics}.keys()))
    write_text(report_path, simple_report("Risk Smoke Evaluation", metrics, "Risk metrics are proxy diagnostics, not safety-evaluation evidence."))
    manifest = create_evaluation_manifest(
        config=config,
        root=root,
        metrics_path=metrics_path,
        report_path=report_path,
        completed=True,
        notes="Risk smoke evaluation; no main table update.",
    )
    write_manifest(output_dir / "evaluation_manifest.json", manifest)
    return EvaluationResult(config.evaluation_name, config.evaluation_type, config.method_name, config.dataset_name, config.scope, metrics, {"risk_score_by_method": {config.method_name: stats}}, {config.filter_manifest_path: sha256_file(resolve_path(config.filter_manifest_path, root))}, {"metrics": metrics_path.as_posix(), "report": report_path.as_posix()}, config.smoke_only, config.protocol_only, True, "Proxy diagnostic only.")
