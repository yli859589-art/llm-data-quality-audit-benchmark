# Main Results Table

Generated from `artifacts/quick_experiment/results.json` in `quick` mode.

Quick mode is a CPU, single-seed smoke test. The table verifies reproducibility and instrumentation; it is not model-quality evidence or a paper-level result.

| Variant | Validation loss mean +/- std | Perplexity mean +/- std | BPC | Next-char accuracy |
| --- | ---: | ---: | ---: | ---: |
| `full_pipeline` | 13.2343 +/- 0.0000 | 559217.60 +/- 0.00 | 19.093 | 0.027 |
| `hdqs_filter` | 13.3115 +/- 0.0000 | 604081.16 +/- 0.00 | 19.204 | 0.025 |
| `raw_noisy_baseline` | 13.2736 +/- 0.0000 | 581636.83 +/- 0.00 | 19.150 | 0.027 |
| `rule_filter_only` | 13.3217 +/- 0.0000 | 610303.43 +/- 0.00 | 19.219 | 0.027 |
