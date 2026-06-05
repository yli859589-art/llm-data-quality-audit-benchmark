# Claim Safety Report

Dataset: WikiText-2 official dev split, real non-fallback local copy.
Metric: final validation perplexity from completed small-model training runs.

Rule: because this phase uses only 3 seeds, every model-quality claim is capped at preliminary trend. No statistically supported claim is made.

## Paired Comparisons

- `dedup_only_vs_raw`: mean raw-minus-baseline diff -0.1046, 95% bootstrap CI [-2.3013, 1.4066], status `trend_only_ci_crosses_zero`, safe claim `trend_only_no_significance_claim`.
- `hdqspp_vs_raw`: mean raw-minus-baseline diff -0.6427, 95% bootstrap CI [-2.0857, 0.1339], status `trend_only_ci_crosses_zero`, safe claim `trend_only_no_significance_claim`.
- `hdqspp_v2_vs_raw`: mean raw-minus-baseline diff -1.5404, 95% bootstrap CI [-3.9939, 1.7919], status `trend_only_ci_crosses_zero`, safe claim `trend_only_no_significance_claim`.
- `hdqspp_v2_no_token_frequency_vs_raw`: mean raw-minus-baseline diff -1.6438, 95% bootstrap CI [-3.4344, 0.6101], status `trend_only_ci_crosses_zero`, safe claim `trend_only_no_significance_claim`.
- `hdqspp_v3_vs_raw`: mean raw-minus-baseline diff -0.6126, 95% bootstrap CI [-2.2043, 1.1888], status `trend_only_ci_crosses_zero`, safe claim `trend_only_no_significance_claim`.
- `length_filter_vs_raw`: mean raw-minus-baseline diff -2.5386, 95% bootstrap CI [-3.7769, -0.9382], status `negative_preliminary_trend`, safe claim `preliminary_trend_only_no_significance_claim`.
- `random_same_keep_rate_vs_raw`: mean raw-minus-baseline diff -0.0844, 95% bootstrap CI [-2.0732, 1.2298], status `trend_only_ci_crosses_zero`, safe claim `trend_only_no_significance_claim`.
