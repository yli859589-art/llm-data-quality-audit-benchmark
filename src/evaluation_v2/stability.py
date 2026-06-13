from __future__ import annotations

from pathlib import Path

from .base import EvaluationConfig, EvaluationResult
from .io import write_json, write_text
from .manifest import create_evaluation_manifest, write_manifest
from .statistics import bootstrap_ci, rank_correlation, summary_stats


def run_stability_evaluation(config: EvaluationConfig, output_dir: Path, root: Path) -> EvaluationResult:
    sample_values = [1.0] if config.scope == "smoke" else []
    metrics = {
        "seed_metric_summary": summary_stats(sample_values),
        "bootstrap_ci": bootstrap_ci(sample_values, samples=config.bootstrap_samples, seed=config.seed),
        "rank_correlation": rank_correlation(sample_values, sample_values),
        "method_ranking_stability": "insufficient_evidence",
        "dataset_sensitivity": "protocol_only",
        "tokenizer_sensitivity": "protocol_only",
        "insufficient_evidence": True,
        "ranking_stability_claim_allowed": False,
        "effectiveness_claim_allowed": False,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "stability_metrics.json"
    report_path = output_dir / "stability_report.md"
    write_json(metrics_path, metrics)
    write_text(
        report_path,
        "# Stability Evaluation\n\n"
        "Step 7 only defines the stability interface. Available smoke inputs are insufficient "
        "for a ranking-stability claim.\n",
    )
    manifest = create_evaluation_manifest(config=config, root=root, metrics_path=metrics_path, report_path=report_path, completed=config.scope == "smoke", notes="Stability protocol/smoke diagnostic with insufficient evidence warning.")
    write_manifest(output_dir / "evaluation_manifest.json", manifest)
    return EvaluationResult(config.evaluation_name, config.evaluation_type, config.method_name, config.dataset_name, config.scope, metrics, {"insufficient_evidence": True}, {}, {"metrics": metrics_path.as_posix(), "report": report_path.as_posix()}, config.smoke_only, config.protocol_only, config.scope == "smoke", "Insufficient evidence.")
