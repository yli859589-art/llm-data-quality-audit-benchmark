from __future__ import annotations

from pathlib import Path
from typing import Any

from .base import EvaluationConfig, EvaluationResult
from .io import read_json, resolve_path, write_csv, write_json, write_text
from .manifest import create_evaluation_manifest, sha256_file, write_manifest
from .reporting import simple_report


def _output_path(manifest: dict[str, Any], name: str, root: Path) -> Path:
    return resolve_path(str(manifest["output_hashes"][name]["path"]), root)


def run_cost_evaluation(config: EvaluationConfig, output_dir: Path, root: Path) -> EvaluationResult:
    filter_manifest = read_json(config.filter_manifest_path, root)
    cost_report = read_json(_output_path(filter_manifest, "cost_report.json", root))
    tokens_seen = None
    training_runtime_seconds = None
    loss_diagnostic = None
    if config.training_manifest_path:
        training_manifest = read_json(config.training_manifest_path, root)
        training_metrics = read_json(str(training_manifest["metrics_path"]), root)
        tokens_seen = training_manifest.get("tokens_seen")
        training_runtime_seconds = training_metrics.get("elapsed_seconds")
        validation_loss = training_metrics.get("validation_loss")
        if validation_loss is not None and tokens_seen:
            loss_diagnostic = float(validation_loss) / max(1.0, float(tokens_seen))
    metrics = {
        "filter_runtime_seconds": cost_report.get("filter_runtime_seconds", 0),
        "training_runtime_seconds": training_runtime_seconds,
        "tokens_seen": tokens_seen,
        "input_docs": filter_manifest.get("input_docs", 0),
        "kept_docs": filter_manifest.get("kept_docs", 0),
        "document_keep_rate": filter_manifest.get("actual_document_keep_rate", 0),
        "token_keep_rate": filter_manifest.get("actual_token_keep_rate", 0),
        "estimated_operations": cost_report.get("estimated_operations", 0),
        "external_dependency_used": cost_report.get("external_dependency_used", False),
        "cost_normalized_loss_diagnostic": loss_diagnostic,
        "compute_cost_proxy": True,
        "real_flops_available": False,
        "main_evidence": False,
        "effectiveness_claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "cost_metrics.json"
    summary_path = output_dir / "cost_summary.csv"
    report_path = output_dir / "cost_evaluation_report.md"
    write_json(metrics_path, metrics)
    write_csv(summary_path, [{"method_name": config.method_name, **metrics}], list({"method_name": config.method_name, **metrics}.keys()))
    write_text(report_path, simple_report("Cost Smoke Evaluation", metrics, "Cost metrics are lightweight diagnostics; real FLOPs are not measured."))
    manifest = create_evaluation_manifest(config=config, root=root, metrics_path=metrics_path, report_path=report_path, completed=True, notes="Cost smoke evaluation; no main table update.")
    write_manifest(output_dir / "evaluation_manifest.json", manifest)
    return EvaluationResult(config.evaluation_name, config.evaluation_type, config.method_name, config.dataset_name, config.scope, metrics, {"cost_proxy": True}, {config.filter_manifest_path: sha256_file(resolve_path(config.filter_manifest_path, root))}, {"metrics": metrics_path.as_posix(), "report": report_path.as_posix()}, config.smoke_only, config.protocol_only, True, "Proxy diagnostic only.")
