# Model Results Summary

Mode: generated from the benchmark configuration in `results.json`.
Seed setting: see the `Seeds` column.
Training budget: see `results_summary.csv` and `token_budget_report.json`.
Interpretation: compact runs validate reproducibility and instrumentation; they are not paper-level model-quality conclusions.
Limitation note: larger datasets, longer training, and fixed method tuning are still required for paper claims.

| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `full_pipeline` | 23 | 13.0679 +/- 0.0000 | 473494.65 +/- 0.00 | 18.853 | 0.031 |
| `hdqs_filter` | 23 | 13.1022 +/- 0.0000 | 490027.00 +/- 0.00 | 18.903 | 0.031 |
| `raw_noisy_baseline` | 23 | 13.2078 +/- 0.0000 | 544605.05 +/- 0.00 | 19.055 | 0.031 |
| `rule_filter_only` | 23 | 13.1207 +/- 0.0000 | 499166.09 +/- 0.00 | 18.929 | 0.031 |
