from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .base import EvaluationConfig, EvaluationResult
from .io import read_json, read_jsonl, resolve_path, write_csv, write_json, write_text
from .manifest import create_evaluation_manifest, sha256_file, write_manifest


def _output_path(manifest: dict[str, Any], name: str, root: Path) -> Path:
    return resolve_path(str(manifest["output_hashes"][name]["path"]), root)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def run_pareto_evaluation(config: EvaluationConfig, output_dir: Path, root: Path) -> EvaluationResult:
    filter_manifest = read_json(config.filter_manifest_path, root)
    component_rows = read_jsonl(_output_path(filter_manifest, "component_scores.jsonl", root))
    frontier_rows = _read_csv(_output_path(filter_manifest, "pareto_frontier.csv", root))
    selected = [row for row in frontier_rows if str(row.get("selected", "")).casefold() == "true"]
    metrics = {
        "utility_risk_frontier_rows": len(frontier_rows),
        "utility_diversity_frontier_rows": len(frontier_rows),
        "utility_cost_frontier_rows": len(frontier_rows),
        "multi_objective_frontier_rows": len([row for row in frontier_rows if row.get("pareto_rank") == "0"]),
        "selected_docs": len(selected),
        "component_score_rows": len(component_rows),
        "method_level_pareto_protocol": True,
        "pareto_improvement_claim_allowed": False,
        "effectiveness_claim_allowed": False,
        "main_evidence": False,
    }
    summary_rows = [
        {
            "doc_id": row.get("doc_id", ""),
            "pareto_rank": row.get("pareto_rank", ""),
            "selected": row.get("selected", ""),
            "utility_score": row.get("utility_score", ""),
            "risk_score": row.get("risk_score", ""),
            "diversity_score": row.get("diversity_score", ""),
            "cost_score": row.get("cost_score", ""),
        }
        for row in frontier_rows
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = output_dir / "pareto_metrics.json"
    summary_path = output_dir / "pareto_frontier_summary.csv"
    report_path = output_dir / "pareto_evaluation_report.md"
    write_json(metrics_path, metrics)
    write_csv(summary_path, summary_rows, ["doc_id", "pareto_rank", "selected", "utility_score", "risk_score", "diversity_score", "cost_score"])
    write_text(
        report_path,
        "# Pareto Smoke Evaluation\n\n"
        "Step 7 reads Step 6 Pareto artifacts and produces diagnostic summaries only. "
        "No Pareto-frontier effectiveness claim is allowed from this smoke output.\n",
    )
    manifest = create_evaluation_manifest(config=config, root=root, metrics_path=metrics_path, report_path=report_path, completed=True, notes="Pareto smoke evaluation; no main table update.")
    write_manifest(output_dir / "evaluation_manifest.json", manifest)
    return EvaluationResult(config.evaluation_name, config.evaluation_type, config.method_name, config.dataset_name, config.scope, metrics, {"pareto_rows": len(frontier_rows)}, {config.filter_manifest_path: sha256_file(resolve_path(config.filter_manifest_path, root))}, {"metrics": metrics_path.as_posix(), "report": report_path.as_posix(), "summary": summary_path.as_posix()}, config.smoke_only, config.protocol_only, True, "Pareto diagnostic only.")
