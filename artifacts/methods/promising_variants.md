# Promising Variant Selection

This table is generated from completed Stage 2.5 diagnostic artifacts. Single-seed rows are treated as diagnostic signals only.

| Variant | Decision | Seed count | PPL signal | Reason |
|---|---|---:|---:|---|
| `ablation_v2_full` | `reject` | 1 | 16.6939758089 | Does not repair the v2 full failure under the current model-training probe. |
| `ablation_v2_without_distribution_preservation` | `needs_more_diagnostics` | 1 | 12.1030523867 | Improves strongly over v2 full and is near strong baselines, but the single seed is not strong enough to promote alongside the best variant. |
| `ablation_v2_without_length_prior` | `needs_more_diagnostics` | 1 | 12.2336926491 | Improves strongly over v2 full and is near strong baselines, but the single seed is not strong enough to promote alongside the best variant. |
| `ablation_v2_without_repetition_penalty` | `keep_debug_only` | 1 | 12.7204214572 | Useful failure diagnosis, but it does not clearly compete with random/dedup. |
| `ablation_v2_without_token_frequency_preservation` | `promote_to_3seed` | 1 | 12.0899364895 | Best seed-1 model-training signal; removes the component most likely to overfit dev token frequencies and beats raw/random/dedup seed-1 references. |

## Component Diagnosis

- `token_frequency_preservation`: Removing it produced the best seed-1 ablation PPL. Action: Remove from v3 full config.
- `distribution_preserving_selection`: Strict preservation improved JS diagnostics but not v2 model PPL. Action: Replace with weak guardrails instead of hard quotas.
- `length_prior`: Removing length prior improved seed-1 ablation PPL. Action: Use only a weak length guardrail to avoid extreme shifts.
- `repetition_penalty`: Removing it helped less than removing token/distribution/length components. Action: Keep a capped, lower-weight repetition score.

## Risk Boundary

WikiText-2 is already curated; strong document filtering can remove useful distributional coverage and may be intrinsically hard to beat versus raw.
