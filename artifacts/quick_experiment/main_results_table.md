# Main Results Table

Generated from `artifacts/quick_experiment/results.json` in `quick` mode.

Quick mode is a CPU, single-seed smoke test. The table verifies reproducibility and preliminary behavior; it is not a paper-level result.

| Variant | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |
| --- | ---: | ---: | ---: | ---: |
| `full_pipeline` | 12.8923 +/- 0.0000 | 397225.39 +/- 0.00 | 18.600 | 0.027 |
| `hdqs_filter` | 12.9380 +/- 0.0000 | 415821.02 +/- 0.00 | 18.666 | 0.027 |
| `raw_noisy_baseline` | 12.8855 +/- 0.0000 | 394545.76 +/- 0.00 | 18.590 | 0.029 |
| `rule_filter_only` | 12.9548 +/- 0.0000 | 422854.30 +/- 0.00 | 18.690 | 0.027 |
