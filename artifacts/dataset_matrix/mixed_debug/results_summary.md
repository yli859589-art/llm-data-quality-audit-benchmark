# Model Results Summary

Mode: generated from the benchmark configuration in `results.json`.
Seed setting: see the `Seeds` column.
Training budget: see `results_summary.csv` and `token_budget_report.json`.
Interpretation: compact runs validate reproducibility and instrumentation; they are not paper-level model-quality conclusions.
Limitation note: larger datasets, longer training, and fixed method tuning are still required for paper claims.

| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `full_pipeline` | 23 | 13.7088 +/- 0.0000 | 898811.78 +/- 0.00 | 19.778 | 0.008 |
| `hdqs_filter` | 23 | 13.6588 +/- 0.0000 | 854940.17 +/- 0.00 | 19.705 | 0.008 |
| `raw_noisy_baseline` | 23 | 13.7381 +/- 0.0000 | 925491.31 +/- 0.00 | 19.820 | 0.008 |
| `rule_filter_only` | 23 | 13.6688 +/- 0.0000 | 863574.66 +/- 0.00 | 19.720 | 0.008 |
