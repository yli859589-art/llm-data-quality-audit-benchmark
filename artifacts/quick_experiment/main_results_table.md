# Main Results Table

Generated from `artifacts/quick_experiment/results.json` in `quick` mode.

Quick mode is a CPU, single-seed smoke test. The table verifies reproducibility and preliminary behavior; it is not a paper-level result.

| Variant | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |
| --- | ---: | ---: | ---: | ---: |
| `full_pipeline` | 12.2969 +/- 0.0000 | 219024.40 +/- 0.00 | 17.741 | 0.029 |
| `hdqs_filter` | 12.3315 +/- 0.0000 | 226734.25 +/- 0.00 | 17.791 | 0.029 |
| `raw_noisy_baseline` | 12.3286 +/- 0.0000 | 226073.44 +/- 0.00 | 17.786 | 0.029 |
| `rule_filter_only` | 12.4156 +/- 0.0000 | 246609.45 +/- 0.00 | 17.912 | 0.029 |
