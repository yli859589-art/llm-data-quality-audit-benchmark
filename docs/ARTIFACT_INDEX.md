# Artifact Index

All public-facing artifacts should follow the claim boundary in
`docs/REPORTING_CONTRACT.md`.

## Release Reports

- `PROJECT_ONE_PAGE.md`
- `PROJECT_SUMMARY.md`
- `TECHNICAL_OVERVIEW.md`
- `DEMO_GUIDE.md`
- `RESUME_BULLETS.md`
- `docs/REPORTING_CONTRACT.md`
- `docs/README.md`
- `docs/PROJECT_PRESENTATION_NOTES.md`
- `docs/FIGURE_INDEX.md`
- `docs/FRESH_CLONE_TEST.md`
- `docs/future_publication_notes/README.md`
- `artifacts/release/claim_hygiene_report.json`
- `artifacts/release/claim_hygiene_report.md`
- `artifacts/release/fresh_unzip_report.json`
- `artifacts/release/fresh_unzip_report.md`
- `artifacts/release/final_release_report.json`
- `artifacts/release/final_release_report.md`

## Data

- `artifacts/data/wikitext2_paper/data_manifest.json`
- `artifacts/data/wikitext2_paper/DATASET_CARD.md`
- `artifacts/data/openwebtext_streaming/data_manifest.json`
- `artifacts/data/openwebtext_streaming/DATASET_CARD.md`
- `artifacts/data/c4_en_streaming/data_manifest.json`
- `artifacts/data/c4_en_streaming/DATASET_CARD.md`
- `artifacts/data/wikitext2_paper/split_integrity_report.json`
- `artifacts/data_manifest.csv`

## Cross-Dataset Audit

- `artifacts/cross_dataset/cross_dataset_results.csv`
- `artifacts/cross_dataset/cross_dataset_results.json`
- `artifacts/cross_dataset/cross_dataset_summary.md`
- `artifacts/cross_dataset/cross_dataset_failures.csv`
- `artifacts/cross_dataset/dataset_status_matrix.csv`
- `artifacts/cross_dataset/cross_dataset_analysis.json`
- `docs/CROSS_DATASET_AUDIT.md`

## Registry

- `artifacts/runs/run_registry.jsonl`
- `artifacts/runs/run_registry.csv`
- `artifacts/runs/run_summary.md`
- `artifacts/runs/migration_log.jsonl`

## Main Results

- `artifacts/tables/main_results.csv`
- `artifacts/stats/main_results.csv`
- `artifacts/stats/main_results.tex`

## Statistics

- `artifacts/stats/significance_tests.csv`
- `artifacts/stats/bootstrap_ci.json`
- `artifacts/stats/effect_sizes.csv`
- `artifacts/stats/method_comparison_summary.csv`
- `artifacts/stats/method_status_report.md`
- `artifacts/stats/claim_safety_report.md`

## Figures

- `artifacts/figures/main_results_leaderboard.svg`
- `artifacts/figures/method_comparison_ci.svg`
- `artifacts/figures/failure_mode_summary.svg`
- `artifacts/figures/artifact_lineage_overview.svg`
- `artifacts/figures/project_pipeline.svg`
- `artifacts/figures/benchmark_protocol.svg`
- `artifacts/figures/cross_dataset_method_comparison.svg`
- `artifacts/figures/cross_dataset_keep_rate.svg`
- `artifacts/figures/cross_dataset_distribution_shift.svg`
- `artifacts/figures/dataset_status_matrix.svg`
- `artifacts/figures/filter_failure_modes_by_dataset.svg`

## Diagnostics

- `artifacts/diagnostics/hdqspp_failure_analysis.csv`
- `artifacts/diagnostics/method_error_cases.csv`
- `artifacts/method_debug/method_debug_results.csv`

## Ablations

- `artifacts/ablations/model_training_ablation_results.csv`
- `artifacts/ablations/v3_model_ablation_results.csv`
- `artifacts/ablations/ablation_results.csv`

## Frozen Configs

- `configs/frozen/hdqspp_frozen_wikitext2.yaml`
- `configs/frozen/hdqspp_v2_frozen_wikitext2.yaml`
- `configs/frozen/hdqspp_v3_frozen_wikitext2.yaml`

## Dashboards

- `docs/EXPERIMENT_DASHBOARD.md`
- `docs/METHOD_DASHBOARD.md`
- `docs/PROJECT_EVIDENCE_MAP.md`

## Environment

- `artifacts/environment/fingerprint.json`

## Legacy Or Superseded Evidence

Legacy and superseded registry rows are retained for audit lineage. The lineage
checker accepts superseded hashes only when a newer row points to the same
artifact path.
