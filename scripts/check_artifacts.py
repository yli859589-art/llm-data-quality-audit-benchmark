from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
artifact_dir = root / "artifacts" / "quick_experiment"
required = [
    "REPORT.md",
    "results.json",
    "dataset_card.json",
    "noise_report.json",
    "hdqs_sweep_report.json",
    "hdqs_sweep_table.md",
    "curriculum_report.json",
    "pipeline_order_report.json",
    "retention_pareto.csv",
    "privacy_utility_tradeoff.csv",
    "token_budget_report.json",
    "privacy_report.json",
    "canary_memorization_report.json",
    "downstream_report.json",
    "downstream_results.csv",
    "generation_quality_report.json",
    "generation_samples.md",
    "attention_benchmark.json",
    "duplicate_clusters.json",
    "environment.json",
    "quality_scores.csv",
    "training_curves.csv",
    "results_summary.csv",
    "results_summary.md",
    "seed_level_results.csv",
    "aggregated_results.csv",
    "statistical_tests.json",
    "main_results_table.md",
    "ablation_table.md",
    "hdqs_interpretation_note.md",
    "multi_dataset_results_table.md",
    "multi_seed_results_table.md",
    "model_scaling_summary.csv",
    "model_scaling_summary.md",
    "model_scaling_table.md",
    "privacy_utility_table.md",
    "downstream_table.md",
    "statistical_tests_table.md",
    "failure_cases.md",
    "error_analysis.md",
    "project_report.md",
    "retention_vs_perplexity.svg",
    "quality_score_distribution.svg",
    "privacy_vs_utility.svg",
    "attention_throughput.svg",
    "training_curves.svg",
    "data_pipeline_summary.svg",
    "pipeline_order_comparison.svg",
    "ablation_heatmap.svg",
    "multi_dataset_perplexity.svg",
    "seed_variance.svg",
    "model_scaling_curve.svg",
    "retention_vs_perplexity_research.svg",
    "noise_type_breakdown.csv",
    "noise_removal_effectiveness.csv",
]
missing = [name for name in required if not (artifact_dir / name).exists()]
if missing:
    raise SystemExit("Missing quick-experiment artifacts: " + ", ".join(missing))

absolute_path = re.compile(rf"(?:[A-Za-z]:(?:\\+|/(?!/))|/{'Users'}/|/{'home'}/[^/]+/)")
for path in artifact_dir.rglob("*"):
    if path.is_file():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if absolute_path.search(text):
            raise SystemExit(f"Artifact contains an absolute local path: {path.relative_to(root)}")

dataset_card = json.loads((artifact_dir / "dataset_card.json").read_text(encoding="utf-8"))
required_card_fields = [
    "dataset_name",
    "source",
    "license_or_usage_note",
    "split",
    "raw_chars",
    "retained_chars",
    "retention_rate",
    "num_docs",
    "num_duplicates_removed",
    "num_near_duplicates_removed",
    "pii_count_before",
    "pii_count_after",
    "random_seed",
    "created_at",
    "code_version/git_commit",
]
missing_fields = [field for field in required_card_fields if field not in dataset_card]
if missing_fields:
    raise SystemExit("Dataset card missing fields: " + ", ".join(missing_fields))

budget = json.loads((artifact_dir / "token_budget_report.json").read_text(encoding="utf-8"))
if not budget["equal_budget_enabled"]:
    raise SystemExit("Quick artifact must use strict equal-budget mode.")
training_lengths = {row["training_characters"] for row in budget["variants"].values()}
if len(training_lengths) != 1:
    raise SystemExit("Compared variants do not use an equal training-character budget.")

dataset_matrix = root / "artifacts" / "dataset_matrix"
for name in ["dataset_matrix_summary.csv", "dataset_matrix_summary.md"]:
    if not (dataset_matrix / name).exists():
        raise SystemExit(f"Missing dataset-matrix artifact: {name}")
for dataset_dir in [path for path in dataset_matrix.iterdir() if path.is_dir()]:
    if not (dataset_dir / "dataset_card.json").exists():
        raise SystemExit(f"Dataset matrix entry missing dataset_card.json: {dataset_dir.name}")

print("Artifact check: ok")
