# Multi-Seed Summary

Mode: `paper-prototype`
Seeds: `23,42,3407`

| Variant | n | Mean perplexity | Std | CI low | CI high |
| --- | ---: | ---: | ---: | ---: | ---: |
| `full_pipeline` | 3 | 287764.9411 | 120974.5041 | 150869.402488199 | 424660.4796179339 |
| `full_pipeline_without_hdqs` | 3 | 275532.6867 | 105193.8014 | 156494.69435974685 | 394570.6790498177 |
| `hdqs_curriculum` | 3 | 289463.5262 | 93060.9117 | 184155.19107153534 | 394771.86142002244 |
| `hdqs_filter` | 3 | 289463.5262 | 93060.9117 | 184155.19107153534 | 394771.86142002244 |
| `raw_noisy_baseline` | 3 | 294610.2230 | 100636.3759 | 180729.4431394326 | 408491.0029268656 |

## Paired Comparisons

Positive mean improvement means the candidate has lower perplexity. Unstable or non-improving directions are reported directly.

- `raw_noisy_baseline_vs_full_pipeline`: `candidate_better`
- `raw_noisy_baseline_vs_hdqs_filter`: `candidate_better`
- `raw_noisy_baseline_vs_hdqs_curriculum`: `candidate_better`
- `full_pipeline_vs_full_pipeline_without_hdqs`: `candidate_better`
