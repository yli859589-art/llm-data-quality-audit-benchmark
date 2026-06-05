# HDQS++ v3 Model-Training Ablation Summary

Top 5 v3 ablations were trained with the same small-model budget. Additional variants are recorded separately as configured_not_run.

| Ablation | Status | Seed | PPL |
|---|---|---:|---:|
| ablation_v3_full | completed_training | 1 | 13.522 |
| ablation_v3_without_soft_weighting | completed_training | 1 | 12.615 |
| ablation_v3_without_keep_rate_calibration | completed_training | 1 | 14.527 |
| ablation_v3_without_quality_diversity_balance | completed_training | 1 | 15.082 |
| ablation_v3_hard_filtering_only | completed_training | 1 | 13.645 |
| raw | reference_completed_training | 1 | 12.700 |
| random_same_keep_rate | reference_completed_training | 1 | 12.110 |
| dedup_only | reference_completed_training | 1 | 12.119 |
| hdqspp_v2_no_token_frequency | reference_completed_training | 1 | 12.090 |
