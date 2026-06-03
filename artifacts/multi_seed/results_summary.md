# Model Results Summary

Mode: generated from the benchmark configuration in `results.json`.
Seed setting: see the `Seeds` column.
Training budget: see `results_summary.csv` and `token_budget_report.json`.
Interpretation: compact runs validate reproducibility and instrumentation; they are not paper-level model-quality conclusions.
Limitation note: larger datasets, longer training, and fixed method tuning are still required for paper claims.

| Variant | Seeds | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |
| --- | --- | ---: | ---: | ---: | ---: |
| `full_pipeline` | 23,42,3407 | 12.5107 +/- 0.4219 | 287764.94 +/- 120974.50 | 18.049 | 0.027 |
| `full_pipeline_without_hdqs` | 23,42,3407 | 12.4769 +/- 0.3874 | 275532.69 +/- 105193.80 | 18.000 | 0.027 |
| `hdqs_curriculum` | 23,42,3407 | 12.5396 +/- 0.3332 | 289463.53 +/- 93060.91 | 18.091 | 0.027 |
| `hdqs_filter` | 23,42,3407 | 12.5396 +/- 0.3332 | 289463.53 +/- 93060.91 | 18.091 | 0.027 |
| `raw_noisy_baseline` | 23,42,3407 | 12.5547 +/- 0.3406 | 294610.22 +/- 100636.38 | 18.113 | 0.023 |
