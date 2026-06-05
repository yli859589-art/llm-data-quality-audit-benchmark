# Method Status Report

- Method status: `honest_audit_framework`
- Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`
- Primary candidate: `hdqspp_v3`
- Reason: Secondary finding `hdqspp_v3_improves_over_v2_trend_but_not_raw`: primary candidate improves over an earlier HDQS version but does not beat raw.
- CCF-C ready: `false`

## Method Comparisons

| Comparison | Mean reference-minus-candidate | CI | Status | Safe claim |
|---|---:|---|---|---|
| `hdqspp_v3_vs_raw` | -0.6126 | [-2.2043, 1.1888] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v3_vs_random_same_keep_rate` | -0.5282 | [-1.4126, -0.0410] | `negative_preliminary_trend` | `preliminary_trend_only_no_significance_claim` |
| `hdqspp_v3_vs_dedup_only` | -0.5080 | [-1.4031, 0.0970] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v3_vs_hdqspp` | 0.0300 | [-0.9562, 1.1649] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v3_vs_hdqspp_v2` | 0.9277 | [-0.6032, 3.1716] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_no_token_frequency_vs_raw` | -1.6438 | [-3.4344, 0.6101] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_no_token_frequency_vs_random_same_keep_rate` | -1.5595 | [-3.3370, 0.0198] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_no_token_frequency_vs_dedup_only` | -1.5392 | [-3.5138, 0.0294] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_no_token_frequency_vs_hdqspp` | -1.0012 | [-2.1310, 0.4763] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_no_token_frequency_vs_hdqspp_v2` | -0.1035 | [-3.8991, 4.6040] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_vs_raw` | -1.5404 | [-3.9939, 1.7919] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_vs_random_same_keep_rate` | -1.4560 | [-4.5842, 0.5621] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_vs_dedup_only` | -1.4357 | [-4.5747, 0.3853] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_v2_vs_hdqspp` | -0.8977 | [-4.1278, 1.7681] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_vs_raw` | -0.6427 | [-2.0857, 0.1339] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_vs_random_same_keep_rate` | -0.5583 | [-1.2060, -0.0125] | `negative_preliminary_trend` | `preliminary_trend_only_no_significance_claim` |
| `hdqspp_vs_dedup_only` | -0.5380 | [-1.3828, 0.2156] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `hdqspp_vs_hdqspp_v2` | 0.8977 | [-1.7681, 4.1278] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `random_same_keep_rate_vs_raw` | -0.0844 | [-2.0732, 1.2298] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
| `dedup_only_vs_raw` | -0.1046 | [-2.3013, 1.4066] | `trend_only_ci_crosses_zero` | `trend_only_no_significance_claim` |
