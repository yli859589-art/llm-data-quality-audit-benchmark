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


def run_diversity_evaluation(config: EvaluationConfig, output_dir: Path, root: Path) -> EvaluationResult:
    filter_manifest = read_json(config.filter_manifest_path, root)
    diversity_report = read_json(_output_path(filter_manifest, "diversity_report.json", root))
    component_rows = read_jsonl(_output_path(filter_manifest, "component_scores.jsonl", root))
    diversity_scores = [float(row.get("diversity_score", 0.0) or 0.0) for row in component_rows]
    stats = summary_stats(diversity_scores)
    metrics = {
        "unique_token_ratio": diversity_report.get("unique_token_ratio", 0),
        "lexical_diversity": diversity_report.get("lexical_diversity", 0),
        "entropy": "proxy_available_in_component_scores",
        "length_mean": diversity_report.get("length_mean", 0),
        "length_std": diversity_report.get("length_std", 0),
        "source_count": diversity_report.get("source_count", 0),
        "coverage_proxy": "hash_vector_and_cluster_proxy",
        "diversity_score_mean": stats["mean"],
        "diversity_score_std": stats["std"],
        "neural_embedding_unavailable": True,
        "proxy_metric": True,
        "main_evidence": False,
        "effectiveness_claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "diversity_metrics.json"
    summary_path = output_dir / "diversity_summary.csv"
    report_path = output_dir / "diversity_evaluation_report.md"
    write_json(metrics_path, metrics)
    write_csv(summary_path, [{"method_name": config.method_name, **metrics}], list({"method_name": config.method_name, **metrics}.keys()))
    write_text(report_path, simple_report("Diversity Smoke Evaluation", metrics, "Diversity metrics are proxy diagnostics, not semantic-diversity evidence."))
    manifest = create_evaluation_manifest(config=config, root=root, metrics_path=metrics_path, report_path=report_path, completed=True, notes="Diversity smoke evaluation; no main table update.")
    write_manifest(output_dir / "evaluation_manifest.json", manifest)
    return EvaluationResult(config.evaluation_name, config.evaluation_type, config.method_name, config.dataset_name, config.scope, metrics, {"diversity_score_by_method": {config.method_name: stats}}, {config.filter_manifest_path: sha256_file(resolve_path(config.filter_manifest_path, root))}, {"metrics": metrics_path.as_posix(), "report": report_path.as_posix()}, config.smoke_only, config.protocol_only, True, "Proxy diagnostic only.")
