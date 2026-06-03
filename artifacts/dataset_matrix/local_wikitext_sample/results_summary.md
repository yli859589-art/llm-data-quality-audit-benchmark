# Model Results Summary

Mode: generated from the benchmark configuration in `results.json`.
Seed setting: see the `Seeds` column.
Training budget: see `results_summary.csv` and `token_budget_report.json`.
Interpretation: compact runs validate reproducibility and instrumentation; they are not paper-level model-quality conclusions.
Limitation note: larger datasets, longer training, and fixed method tuning are still required for paper claims.

| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `full_pipeline` | 23 | 13.6461 +/- 0.0000 | 844138.95 +/- 0.00 | 19.687 | 0.008 |
| `hdqs_filter` | 23 | 13.7970 +/- 0.0000 | 981624.07 +/- 0.00 | 19.905 | 0.008 |
| `raw_noisy_baseline` | 23 | 13.8141 +/- 0.0000 | 998585.94 +/- 0.00 | 19.930 | 0.008 |
| `rule_filter_only` | 23 | 13.7716 +/- 0.0000 | 957009.21 +/- 0.00 | 19.868 | 0.008 |
