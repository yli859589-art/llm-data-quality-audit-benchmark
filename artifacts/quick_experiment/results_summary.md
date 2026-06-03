# Model Results Summary

Mode: generated from the benchmark configuration in `results.json`.
Seed setting: see the `Seeds` column.
Training budget: see `results_summary.csv` and `token_budget_report.json`.
Interpretation: compact runs validate reproducibility and instrumentation; they are not paper-level model-quality conclusions.
Limitation note: larger datasets, longer training, and fixed method tuning are still required for paper claims.

| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `full_pipeline` | 23 | 13.2343 +/- 0.0000 | 559217.60 +/- 0.00 | 19.093 | 0.027 |
| `hdqs_filter` | 23 | 13.3115 +/- 0.0000 | 604081.16 +/- 0.00 | 19.204 | 0.025 |
| `raw_noisy_baseline` | 23 | 13.2736 +/- 0.0000 | 581636.83 +/- 0.00 | 19.150 | 0.027 |
| `rule_filter_only` | 23 | 13.3217 +/- 0.0000 | 610303.43 +/- 0.00 | 19.219 | 0.027 |
