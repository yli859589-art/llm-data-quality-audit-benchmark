# HDQS++ Sweep Table

Mode: generated from the benchmark configuration in `results.json`.
Seed setting: not a model-training table; see sibling `results.json`.
Training budget: data-selection diagnostic; see `token_budget_report.json`.
Interpretation: threshold and top-k rows evaluate deterministic data-selection behavior.
Limitation note: this table does not prove HDQS++ improves model quality without larger training runs.

Threshold and top-k rows are deterministic data-selection diagnostics.

| Type | Setting | Retained docs | Retained chars | Mean HDQS | PII-like hits |
| --- | --- | ---: | ---: | ---: | ---: |
| threshold | 0.74 | 38 | 18183 | 0.863 | 18 |
| threshold | 0.76 | 35 | 16228 | 0.872 | 9 |
| threshold | 0.78 | 34 | 15725 | 0.875 | 6 |
| threshold | 0.8 | 34 | 15725 | 0.875 | 6 |
| threshold | 0.82 | 24 | 11033 | 0.902 | 6 |
| threshold | 0.84 | 22 | 10085 | 0.909 | 6 |
| threshold | 0.86 | 21 | 9545 | 0.912 | 6 |
| top-k | 0.25 | 13 | 5649 | 0.926 | 0 |
| top-k | 0.5 | 25 | 11464 | 0.898 | 6 |
| top-k | 0.75 | 37 | 17534 | 0.866 | 15 |
