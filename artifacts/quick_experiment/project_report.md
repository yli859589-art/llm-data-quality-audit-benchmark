# Project Report

This generated report summarizes the current research prototype artifacts.

## Positioning

Resume-ready and CCF-C-convertible research prototype; not a completed paper.

## Quick Evidence

- Mode: `quick`
- Seed setting: `23`
- Training budget: `18000` characters per compared variant
- Dataset: `tiny_shakespeare`
- HDQS standalone status: `standalone_hdqs_not_better_than_raw_in_this_quick_run`
- Trained variants: `full_pipeline, hdqs_filter, raw_noisy_baseline, rule_filter_only`

Interpretation: quick-mode results validate reproducibility and instrumentation.
Limitation note: compact results are not paper-level model-quality evidence.

## Generated Tables

- `main_results_table.md`
- `multi_dataset_results_table.md`
- `multi_seed_results_table.md`
- `privacy_utility_table.md`
- `downstream_table.md`
- `statistical_tests_table.md`

## Generated Figures

- `retention_vs_perplexity.svg`
- `privacy_vs_utility.svg`
- `pipeline_order_comparison.svg`
- `model_scaling_curve.svg`
- `hdqs_sweep_heatmap.svg`
- `privacy_retention_pareto.svg`

## Remaining Full Experiments

- Run explicit-network or local WikiText-2/OpenWebText/C4 samples.
- Scale full mode across larger datasets, longer budgets, and model sizes.
- Tune HDQS++ weights on a development split.
