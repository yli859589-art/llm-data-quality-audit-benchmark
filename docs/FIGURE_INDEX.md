# Figure Index

All figures follow `docs/REPORTING_CONTRACT.md`. Do not claim from any figure
that HDQS++ v3 outperforms raw under the current fair benchmark.

| Figure | Source artifact | Generating script | What it shows | Safe interpretation | What not to claim | Scope/status |
|---|---|---|---|---|---|---|
| `artifacts/figures/project_pipeline.svg` | `artifacts/data/wikitext2_paper/data_manifest.json` | `scripts/generate_project_dashboard.py` | End-to-end audit pipeline | Shows reproducibility structure | Not a method win | release/dashboard artifact |
| `artifacts/figures/benchmark_protocol.svg` | `configs/experiments/dev.yaml` | `scripts/generate_project_dashboard.py` | Fairness controls | Shows budget/tokenizer constraints | Not paper-scale proof | release/dashboard artifact |
| `artifacts/figures/main_results_leaderboard.svg` | `artifacts/stats/main_results.csv` | `scripts/generate_project_dashboard.py` | WikiText-2 mean PPL ranking | Raw is strongest current mean baseline | Do not claim HDQS++ over raw | WikiText-2 official split, completed_training |
| `artifacts/figures/method_comparison_ci.svg` | `artifacts/stats/method_comparison_summary.csv` | `scripts/generate_method_dashboard.py` | Confidence intervals for method comparisons | Claims remain bounded by 3 seeds | Do not claim statistical improvement over raw | WikiText-2 official split, completed_training |
| `artifacts/figures/failure_mode_summary.svg` | `artifacts/stats/main_results.csv` | `scripts/generate_project_dashboard.py` | PPL deltas versus raw | Positive delta means worse than raw | Do not hide method failure | WikiText-2 official split, release/dashboard artifact |
| `artifacts/figures/cross_dataset_method_comparison.svg` | `artifacts/cross_dataset/cross_dataset_results.csv` | `scripts/analyze_cross_dataset_audit.py` | Mean PPL by dataset/method | Cross-dataset audit evidence | Do not compare across datasets without controls | WikiText-2 + streaming samples, completed_training |
| `artifacts/figures/dataset_status_matrix.svg` | `artifacts/cross_dataset/dataset_status_matrix.csv` | `scripts/analyze_cross_dataset_audit.py` | Dataset status and availability | OpenWebText/C4 are streaming samples | Do not call them full datasets | cross-dataset audit |
| `artifacts/figures/artifact_lineage_overview.svg` | `artifacts/runs/run_registry.csv` | `scripts/generate_project_dashboard.py` | Registry status counts | Failed/superseded rows are retained | Do not delete failures to beautify results | release/dashboard artifact |
| `artifacts/figures/keep_rate_vs_ppl.svg` | `artifacts/tables/main_results.csv` | `scripts/generate_method_dashboard.py` | Keep rate vs validation PPL | Filtering behavior can be fragile | Not evidence of a winning filter | WikiText-2 official split |
| `artifacts/figures/component_effects_v3.svg` | `artifacts/ablations/v3_model_ablation_results.csv` | `scripts/generate_method_dashboard.py` | V3 component diagnostics | Diagnostic support only | Not a primary method claim | diagnostic artifact |
| `artifacts/figures/promising_variant_selection.svg` | `artifacts/methods/promising_variants.csv` | `scripts/generate_method_dashboard.py` | Variant selection trace | Shows why v3 was selected for audit | Not a final success claim | diagnostic artifact |
| `artifacts/figures/cross_dataset_keep_rate.svg` | `artifacts/cross_dataset/cross_dataset_results.csv` | `scripts/analyze_cross_dataset_audit.py` | Keep rates across audit datasets | Compare within controlled settings | Not full-dataset evidence | streaming-sample audit |
| `artifacts/figures/cross_dataset_distribution_shift.svg` | `artifacts/cross_dataset/cross_dataset_results.csv` | `scripts/analyze_cross_dataset_audit.py` | Distribution-shift proxy | Useful diagnostic | Not proof of improved pretraining | streaming-sample audit |
| `artifacts/figures/filter_failure_modes_by_dataset.svg` | `artifacts/cross_dataset/cross_dataset_failures.csv` | `scripts/analyze_cross_dataset_audit.py` | Failure modes by dataset | Failures remain visible | Do not hide failed rows | cross-dataset audit |
