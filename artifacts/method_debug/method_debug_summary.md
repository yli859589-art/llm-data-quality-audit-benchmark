# Method Debug Summary

This is a proxy-only sandbox. It is excluded from main_results and does not support model-quality claims.

| Method | Retention | Token JS vs raw | Length JS vs raw | Proxy loss |
|---|---:|---:|---:|---:|
| hdqspp | 0.601 | 0.036882 | 0.035023 | 10.7667 |
| hdqspp_v2 | 0.851 | 0.010112 | 0.003600 | 10.5780 |
| v2_without_length_prior | 0.851 | 0.010228 | 0.001219 | 10.5819 |
| v2_without_distribution_preservation | 0.851 | 0.015455 | 0.004308 | 10.5985 |
| v2_without_token_frequency_preservation | 0.851 | 0.011124 | 0.000079 | 10.8032 |
| v2_without_repetition_penalty | 0.851 | 0.010892 | 0.005685 | 10.5550 |
| v2_hard_filtering | 0.601 | 0.036700 | 0.027671 | 10.4308 |
| v2_soft_weighting_curriculum | 0.901 | 0.007584 | 0.002351 | 10.6364 |
| random_same_keep_rate | 0.599 | 0.017667 | 0.001188 | 10.6962 |
| dedup_only | 0.992 | 0.000000 | 0.000426 | 10.7202 |
