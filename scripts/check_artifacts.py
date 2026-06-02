from __future__ import annotations

import json
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
artifact_dir = root / "artifacts" / "quick_experiment"
required = [
    "REPORT.md",
    "results.json",
    "dataset_card.json",
    "noise_report.json",
    "token_budget_report.json",
    "privacy_report.json",
    "downstream_report.json",
    "attention_benchmark.json",
    "duplicate_clusters.json",
    "environment.json",
    "quality_scores.csv",
    "training_curves.csv",
    "results_summary.csv",
    "results_summary.md",
    "main_results_table.md",
    "ablation_table.md",
    "retention_vs_perplexity.svg",
    "quality_score_distribution.svg",
    "privacy_vs_utility.svg",
    "attention_throughput.svg",
    "training_curves.svg",
    "data_pipeline_summary.svg",
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

print("Artifact check: ok")
