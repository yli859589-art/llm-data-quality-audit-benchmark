from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark.reporting import (
    write_named_bar_chart,
    write_scatter_chart,
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


artifact_dir = root / "artifacts" / "quick_experiment"
payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))

pipeline_rows = payload.get("pipeline_order_report", {}).get("rows", [])
write_named_bar_chart(
    artifact_dir / "pipeline_order_comparison.svg",
    [
        (str(row["pipeline_order"]), float(row["retained_documents"]))
        for row in pipeline_rows
    ],
    "Pipeline order comparison",
    "Retained documents",
)
ablation = payload["data_quality_ablation"]
write_named_bar_chart(
    artifact_dir / "ablation_heatmap.svg",
    [(name, float(row["mean_hdqs"])) for name, row in ablation.items()],
    "Ablation mean HDQS",
    "Mean HDQS",
)
hdqs_rows = payload.get("hdqs_sweep_report", {}).get("threshold_rows", [])
write_named_bar_chart(
    artifact_dir / "hdqs_sweep_heatmap.svg",
    [
        (f"threshold={row['threshold']}", float(row["mean_hdqs_retained"]))
        for row in hdqs_rows
    ]
    or [("not_run", 0.0)],
    "HDQS sweep diagnostic heatmap",
    "Mean retained HDQS",
)
dataset_rows = _read_csv(root / "artifacts" / "dataset_matrix" / "dataset_matrix_summary.csv")
write_named_bar_chart(
    artifact_dir / "multi_dataset_perplexity.svg",
    [
        (
            row["dataset_key"],
            float(row["full_pipeline_perplexity"])
            if row.get("full_pipeline_perplexity") not in {"", "None"}
            else 0.0,
        )
        for row in dataset_rows
    ]
    or [("not_run", 0.0)],
    "Multi-dataset full-pipeline perplexity",
    "Perplexity",
)
seed_rows = _read_csv(artifact_dir / "aggregated_results.csv")
write_named_bar_chart(
    artifact_dir / "seed_variance.svg",
    [(row["variant"], float(row.get("std") or 0.0)) for row in seed_rows] or [("not_run", 0.0)],
    "Seed variance",
    "Perplexity std",
)
model_rows = _read_csv(artifact_dir / "model_scaling_summary.csv")
write_named_bar_chart(
    artifact_dir / "model_scaling_curve.svg",
    [
        (row["model"], float(row["estimated_parameter_count"]))
        for row in model_rows
    ]
    or [("not_run", 0.0)],
    "Configured model scaling",
    "Estimated parameters",
)
write_scatter_chart(
    artifact_dir / "retention_vs_perplexity_research.svg",
    [
        (
            row["variant"],
            float(row["retention_ratio"]),
            float(row["perplexity_mean"] or 0.0),
        )
        for row in _read_csv(artifact_dir / "retention_pareto.csv")
        if row.get("status") == "trained"
    ]
    or [("not_run", 0.0, 0.0)],
    "Retention versus perplexity",
    "Retention ratio",
    "Perplexity",
)
write_scatter_chart(
    artifact_dir / "privacy_retention_pareto.svg",
    [
        (
            row["variant"],
            float(row["retention_ratio"]),
            float(row["pii_like_hits"]),
        )
        for row in _read_csv(artifact_dir / "retention_pareto.csv")
    ]
    or [("not_run", 0.0, 0.0)],
    "Privacy-retention Pareto",
    "Retention ratio",
    "Residual PII-like hits",
)
print(f"Research figures regenerated in {artifact_dir}")
