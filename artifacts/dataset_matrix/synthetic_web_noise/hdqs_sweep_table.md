# HDQS++ Sweep Table

Mode: generated from the benchmark configuration in `results.json`.
Seed setting: not a model-training table; see sibling `results.json`.
Training budget: data-selection diagnostic; see `token_budget_report.json`.
Interpretation: threshold and top-k rows evaluate deterministic data-selection behavior.
Limitation note: this table does not prove HDQS++ improves model quality without larger training runs.

Threshold and top-k rows are deterministic data-selection diagnostics.

| Type | Setting | Retained docs | Retained chars | Mean HDQS | PII-like hits |
| --- | --- | ---: | ---: | ---: | ---: |
| threshold | 0.74 | 13 | 6168 | 0.849 | 14 |
| threshold | 0.76 | 13 | 6168 | 0.849 | 14 |
| threshold | 0.78 | 10 | 4216 | 0.874 | 5 |
| threshold | 0.8 | 9 | 3727 | 0.883 | 3 |
| threshold | 0.82 | 8 | 3314 | 0.893 | 3 |
| threshold | 0.84 | 7 | 2816 | 0.902 | 3 |
| threshold | 0.86 | 7 | 2816 | 0.902 | 3 |
| top-k | 0.25 | 5 | 2066 | 0.910 | 0 |
| top-k | 0.5 | 9 | 3727 | 0.883 | 3 |
| top-k | 0.75 | 14 | 6383 | 0.832 | 14 |
