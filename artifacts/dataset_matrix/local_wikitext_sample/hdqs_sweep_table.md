# HDQS++ Sweep Table

Mode: generated from the benchmark configuration in `results.json`.
Seed setting: not a model-training table; see sibling `results.json`.
Training budget: data-selection diagnostic; see `token_budget_report.json`.
Interpretation: threshold and top-k rows evaluate deterministic data-selection behavior.
Limitation note: this table does not prove HDQS++ improves model quality without larger training runs.

Threshold and top-k rows are deterministic data-selection diagnostics.

| Type | Setting | Retained docs | Retained chars | Mean HDQS | PII-like hits |
| --- | --- | ---: | ---: | ---: | ---: |
| threshold | 0.74 | 9 | 4621 | 0.859 | 9 |
| threshold | 0.76 | 9 | 4621 | 0.859 | 9 |
| threshold | 0.78 | 6 | 2666 | 0.902 | 0 |
| threshold | 0.8 | 6 | 2666 | 0.902 | 0 |
| threshold | 0.82 | 6 | 2666 | 0.902 | 0 |
| threshold | 0.84 | 4 | 1679 | 0.940 | 0 |
| threshold | 0.86 | 4 | 1679 | 0.940 | 0 |
| top-k | 0.25 | 4 | 1679 | 0.940 | 0 |
| top-k | 0.5 | 7 | 3323 | 0.884 | 3 |
| top-k | 0.75 | 10 | 4836 | 0.835 | 9 |
