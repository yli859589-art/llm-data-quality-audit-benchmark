# Failure Taxonomy

This taxonomy preserves observed, hypothesized, protocol-only, and insufficient-evidence failure modes.
It does not present URD as a method that fixes all failures.

| Failure Type | Evidence Status | Description |
|---|---|---|
| `proxy_utility_mismatch` | `hypothesized` | Filter proxy may not track actual training utility. |
| `overfiltering` | `hypothesized` | Aggressive retention can remove useful tokens. |
| `diversity_collapse` | `hypothesized` | Filtering can reduce lexical or semantic coverage. |
| `domain_shift` | `hypothesized` | Selection can move data away from the validation distribution. |
| `tokenizer_budget_mismatch` | `protocol_only` | Whitespace/char/BPE budgets can disagree. |
| `weak_baseline_illusion` | `protocol_only` | Method gains are unsafe without raw/random/dedup/length controls. |
| `small_model_artifact` | `protocol_only` | Tiny/small behavior may not transfer to larger scales. |
| `seed_instability` | `insufficient_evidence` | Multi-seed evidence is not yet complete. |
| `smoke_main_leakage_risk` | `observed_risk_controlled` | Checks keep smoke/protocol artifacts out of main tables. |
| `protocol_completed_confusion` | `observed_risk_controlled` | Manifests separate protocol_only from completed outputs. |
| `negative_result_preservation` | `observed` | Historical negative results are retained as audit evidence. |
| `hdqspp_historical_failure` | `observed` | HDQS++ v3 did not outperform raw in the current historical fair benchmark evidence. |
| `insufficient_evidence_categories` | `observed` | Step 8 explicitly marks smoke/protocol findings as insufficient. |

## Claim Boundary

The taxonomy is a mechanism-analysis scaffold. It is not a full-scale mechanism conclusion.
