# Method Diagnostics

## HDQS++ v2 Failure Diagnosis

v2 full reduced token/length distribution shift versus v1, but model-training results still underperformed raw. Stage 2.5 ablations identified token-frequency preservation as the strongest harmful component, with strict distribution preservation and length prior also suspicious.

## Promising Variant Selection

| Variant | Decision | PPL signal |
|---|---|---:|
| `ablation_v2_full` | `reject` | 16.6939758089 |
| `ablation_v2_without_distribution_preservation` | `needs_more_diagnostics` | 12.1030523867 |
| `ablation_v2_without_length_prior` | `needs_more_diagnostics` | 12.2336926491 |
| `ablation_v2_without_repetition_penalty` | `keep_debug_only` | 12.7204214572 |
| `ablation_v2_without_token_frequency_preservation` | `promote_to_3seed` | 12.0899364895 |

## HDQS++ v3 Repair

- Removed token-frequency preservation.
- Replaced strict distribution preservation with weak length/bin guardrails.
- Replaced hard filtering emphasis with calibrated soft selection.
- Kept base quality, quality/diversity balance, and capped repetition.

## Current Boundary

If v3 does not outperform raw, the safe interpretation is diagnostic/audit value, not a model-quality improvement claim.
