from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

root = Path(__file__).resolve().parents[1]
quick_dir = root / "artifacts" / "quick_experiment"
dataset_matrix = root / "artifacts" / "dataset_matrix"
multi_seed = root / "artifacts" / "multi_seed"
model_scaling = root / "artifacts" / "model_scaling"
research = root / "artifacts" / "research"
readiness_bases = [
    root / "artifacts" / "data",
    root / "artifacts" / "baselines",
    root / "artifacts" / "runs",
    root / "artifacts" / "frozen",
    root / "artifacts" / "ablations",
    root / "artifacts" / "stats",
    root / "artifacts" / "tables",
    root / "artifacts" / "figures",
    root / "artifacts" / "model_cards",
]


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON artifact: {path.relative_to(root)}") from exc


def _load_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    except csv.Error as exc:
        raise SystemExit(f"Invalid CSV artifact: {path.relative_to(root)}") from exc


def _require(path: Path, label: str) -> None:
    if not path.exists():
        raise SystemExit(f"Missing {label}: {path.relative_to(root)}")


def _require_fields(payload: dict[str, Any], fields: list[str], label: str) -> None:
    missing = [field for field in fields if field not in payload]
    if missing:
        raise SystemExit(f"{label} missing fields: {', '.join(missing)}")


def _check_no_absolute_paths() -> None:
    absolute_path = re.compile(rf"(?:[A-Za-z]:(?:\\+|/(?!/))|/{'Users'}/|/{'home'}/[^/]+/)")
    for base in [quick_dir, dataset_matrix, multi_seed, model_scaling, research, *readiness_bases]:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            if absolute_path.search(text):
                raise SystemExit(
                    f"Artifact contains an absolute local path: {path.relative_to(root)}"
                )


def _check_no_unlabeled_placeholders() -> None:
    forbidden = {"fake_result", "placeholder_without_label"}
    for base in [quick_dir, dataset_matrix, multi_seed, model_scaling, research, *readiness_bases]:
        if not base.exists():
            continue
        for path in base.rglob("*.json"):
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                if token in text:
                    raise SystemExit(
                        f"Artifact contains forbidden placeholder token `{token}`: "
                        f"{path.relative_to(root)}"
                    )


def _check_table_metadata(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    required_phrases = ["Mode:", "Seed setting:", "Training budget:", "Interpretation:"]
    missing = [phrase for phrase in required_phrases if phrase not in text]
    if missing:
        raise SystemExit(
            f"Markdown table missing metadata {missing}: {path.relative_to(root)}"
        )


quick_required = [
    "REPORT.md",
    "results.json",
    "dataset_card.json",
    "noise_report.json",
    "hdqs_sweep_report.json",
    "hdqs_sweep_table.md",
    "hdqs_best_config.json",
    "hdqs_failure_cases.md",
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
    "research_readiness_summary.md",
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
    "hdqs_sweep_heatmap.svg",
    "privacy_retention_pareto.svg",
    "noise_type_breakdown.csv",
    "noise_removal_effectiveness.csv",
]
for name in quick_required:
    _require(quick_dir / name, "quick-experiment artifact")

results = _load_json(quick_dir / "results.json")
_require_fields(
    results,
    [
        "project",
        "mode",
        "configuration",
        "dataset_card",
        "token_budget_report",
        "model_runs",
        "model_summary",
        "privacy_report",
        "limitations",
    ],
    "quick results.json",
)
dataset_card = _load_json(quick_dir / "dataset_card.json")
_require_fields(
    dataset_card,
    [
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
    ],
    "quick dataset_card.json",
)
budget = _load_json(quick_dir / "token_budget_report.json")
if not budget["equal_budget_enabled"]:
    raise SystemExit("Quick artifact must use strict equal-budget mode.")
training_lengths = {row["training_characters"] for row in budget["variants"].values()}
if len(training_lengths) != 1:
    raise SystemExit("Compared variants do not use an equal training-character budget.")

for name in ["dataset_matrix_summary.csv", "dataset_matrix_summary.md"]:
    _require(dataset_matrix / name, "dataset-matrix artifact")
for name in ["paper_prototype_summary.csv", "paper_prototype_summary.md"]:
    _require(dataset_matrix / name, "paper-prototype artifact")
for dataset_dir in [path for path in dataset_matrix.iterdir() if path.is_dir()]:
    card_path = dataset_dir / "dataset_card.json"
    fallback_path = dataset_dir / "fallback_report.json"
    results_path = dataset_dir / "results.json"
    _require(card_path, "dataset-matrix dataset card")
    _require(fallback_path, "dataset-matrix fallback report")
    _require(results_path, "dataset-matrix results file")
    card = _load_json(card_path)
    fallback = _load_json(fallback_path)
    row_results = _load_json(results_path)
    _require_fields(
        fallback,
        [
            "dataset_key",
            "dataset_name",
            "used_fallback",
            "status",
            "fallback_reason",
            "command",
            "source",
            "license_note",
        ],
        f"{dataset_dir.name} fallback_report.json",
    )
    _require_fields(
        row_results,
        ["mode", "dataset_key", "status", "used_fallback", "command"],
        f"{dataset_dir.name} results.json",
    )
    if fallback["used_fallback"] and row_results["status"] != "fallback_recorded":
        raise SystemExit(f"Fallback dataset is not marked fallback_recorded: {dataset_dir.name}")
    if "fallback" not in card:
        raise SystemExit(f"Dataset card missing fallback field: {dataset_dir.name}")

for name in [
    "seed_level_results.csv",
    "aggregated_results.csv",
    "statistical_tests.json",
    "multi_seed_summary.md",
    "seed_variance.svg",
]:
    _require(multi_seed / name, "multi-seed artifact")
tests = _load_json(multi_seed / "statistical_tests.json")
expected_comparisons = {
    "raw_noisy_baseline_vs_full_pipeline",
    "raw_noisy_baseline_vs_hdqs_filter",
    "raw_noisy_baseline_vs_hdqs_curriculum",
    "full_pipeline_vs_full_pipeline_without_hdqs",
}
if not expected_comparisons.issubset(set(tests.get("paired", {}))):
    raise SystemExit("Multi-seed statistical_tests.json missing required paired comparisons.")

for name in ["model_scaling_summary.csv", "model_scaling_summary.md", "scaling_curve.svg"]:
    _require(model_scaling / name, "model-scaling artifact")

research_required = [
    "multi_dataset_results_table.md",
    "multi_seed_results_table.md",
    "model_scaling_table.md",
    "privacy_utility_table.md",
    "downstream_table.md",
    "statistical_tests_table.md",
    "research_readiness_summary.md",
    "error_analysis.md",
    "ablation_heatmap.svg",
    "multi_dataset_perplexity.svg",
    "pipeline_order_comparison.svg",
    "data_pipeline_summary.svg",
    "hdqs_sweep_heatmap.svg",
    "privacy_retention_pareto.svg",
]
for name in research_required:
    _require(research / name, "research artifact")

experiment_readiness_required = [
    root / "artifacts" / "data_manifest.json",
    root / "artifacts" / "data_manifest.csv",
    root / "artifacts" / "data_manifest.md",
    root / "artifacts" / "data" / "wikitext2_smoke" / "data_manifest.json",
    root / "artifacts" / "data" / "wikitext2_smoke" / "data_manifest.csv",
    root / "artifacts" / "data" / "wikitext2_smoke" / "data_manifest.md",
    root / "artifacts" / "baselines" / "wikitext2_smoke" / "raw" / "seed_13" / "metrics.json",
    root
    / "artifacts"
    / "baselines"
    / "wikitext2_smoke"
    / "random_same_keep_rate"
    / "seed_13"
    / "metrics.json",
    root / "artifacts" / "runs" / "run_registry.csv",
    root / "artifacts" / "runs" / "run_registry.jsonl",
    root / "artifacts" / "runs" / "run_summary.md",
    root / "artifacts" / "frozen" / "hdqspp_frozen_wikitext2_smoke.json",
    root / "artifacts" / "ablations" / "smoke" / "ablation_results.csv",
    root / "artifacts" / "ablations" / "smoke" / "ablation_results.json",
    root / "artifacts" / "stats" / "main_results.csv",
    root / "artifacts" / "stats" / "main_results.tex",
    root / "artifacts" / "stats" / "significance_tests.json",
    root / "artifacts" / "stats" / "claim_safety_report.md",
    root / "artifacts" / "tables" / "baseline_comparison.md",
    root / "artifacts" / "tables" / "significance_summary.md",
    root / "artifacts" / "figures" / "baseline_retention.svg",
    root / "artifacts" / "figures" / "claim_support_boundary.svg",
    root / "artifacts" / "model_cards" / "tiny.json",
    root / "artifacts" / "model_cards" / "small.json",
    root / "artifacts" / "model_cards" / "medium.json",
    root / "artifacts" / "experiment_readiness_report.json",
]
for path in experiment_readiness_required:
    _require(path, "experiment-readiness artifact")

manifest = _load_json(root / "artifacts" / "data_manifest.json")
if not manifest["used_fallback"]:
    raise SystemExit("Smoke data manifest should explicitly label local fallback usage.")
if manifest["required_real_data"]:
    raise SystemExit("Smoke data manifest must not be labeled as required real data.")
registry_rows = _load_csv(root / "artifacts" / "runs" / "run_registry.csv")
if len(registry_rows) < 8:
    raise SystemExit("Run registry has too few baseline rows.")
readiness = _load_json(root / "artifacts" / "experiment_readiness_report.json")
if readiness["readiness_level"] == "CCF_C_EXPERIMENT_READY":
    raise SystemExit("Readiness report must not claim final CCF-C readiness.")

for table_name in [
    "results_summary.md",
    "main_results_table.md",
    "ablation_table.md",
    "hdqs_sweep_table.md",
    "multi_dataset_results_table.md",
    "multi_seed_results_table.md",
    "model_scaling_table.md",
    "privacy_utility_table.md",
    "downstream_table.md",
    "statistical_tests_table.md",
]:
    _check_table_metadata(quick_dir / table_name)
for table_name in [
    "dataset_matrix_summary.md",
    "paper_prototype_summary.md",
]:
    _check_table_metadata(dataset_matrix / table_name)
for table_name in [
    "multi_dataset_results_table.md",
    "multi_seed_results_table.md",
    "model_scaling_table.md",
    "privacy_utility_table.md",
    "downstream_table.md",
    "statistical_tests_table.md",
]:
    _check_table_metadata(research / table_name)

for csv_path in [
    quick_dir / "retention_pareto.csv",
    quick_dir / "privacy_utility_tradeoff.csv",
    quick_dir / "downstream_results.csv",
    dataset_matrix / "paper_prototype_summary.csv",
    multi_seed / "aggregated_results.csv",
    model_scaling / "model_scaling_summary.csv",
    root / "artifacts" / "runs" / "run_registry.csv",
    root / "artifacts" / "stats" / "main_results.csv",
    root / "artifacts" / "ablations" / "smoke" / "ablation_results.csv",
]:
    if not _load_csv(csv_path):
        raise SystemExit(f"CSV artifact has no rows: {csv_path.relative_to(root)}")

_check_no_absolute_paths()
_check_no_unlabeled_placeholders()
print("Artifact check: ok")
