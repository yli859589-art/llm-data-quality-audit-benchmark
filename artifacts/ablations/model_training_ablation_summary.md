# Model-Training Ablation Summary

Top 5 HDQS++ v2 ablations were trained with the same small-model budget. Deferred variants are recorded separately as configured_not_run.

| Ablation | Status | Seed | PPL |
|---|---|---:|---:|
| ablation_v2_full | completed_training | 1 | 16.694 |
| ablation_v2_without_length_prior | completed_training | 1 | 12.234 |
| ablation_v2_without_distribution_preservation | completed_training | 1 | 12.103 |
| ablation_v2_without_token_frequency_preservation | completed_training | 1 | 12.090 |
| ablation_v2_without_repetition_penalty | completed_training | 1 | 12.720 |
| random_same_keep_rate | reference_completed_training | 1 | 12.110 |
| dedup_only | reference_completed_training | 1 | 12.119 |
