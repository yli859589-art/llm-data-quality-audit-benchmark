# Statistical Tests

Mode: `paper-prototype` paired comparisons.
Seed setting: `23,42,3407`.
Training budget: compact paper-prototype budget per seed/variant.
Interpretation: positive mean improvement means lower perplexity for the candidate, but interval width must be inspected.
Limitation note: current intervals are not strong enough for final paper claims.

| comparison | count | mean | std | ci95_low | ci95_high | lower_is_better | positive_mean_improvement | status | direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| raw_noisy_baseline_vs_full_pipeline | 3 | 6845.2819800826355 | 20391.429035203917 | -16229.792223484186 | 29920.35618364946 | True | True | ok | candidate_better |
| raw_noisy_baseline_vs_hdqs_filter | 3 | 5146.696787370165 | 15521.814457163697 | -12417.889772733412 | 22711.28334747374 | True | True | ok | candidate_better |
| raw_noisy_baseline_vs_hdqs_curriculum | 3 | 5146.696787370165 | 15521.814457163697 | -12417.889772733412 | 22711.28334747374 | True | True | ok | candidate_better |
| full_pipeline_vs_full_pipeline_without_hdqs | 3 | 12232.254348284177 | 16684.26777086121 | -6647.771969643318 | 31112.28066621167 | True | True | ok | candidate_better |
