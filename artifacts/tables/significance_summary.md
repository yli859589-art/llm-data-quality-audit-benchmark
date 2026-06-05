# Significance Summary

Mode: registry audit
Seed setting: requires at least three seeds for supported claims
Training budget: model-training metrics are absent unless explicitly recorded
Interpretation: unsupported rows are claim-safety warnings

| Dataset | Baseline | Rows | Claim status |
|---|---|---:|---|
| wikitext2_paper | dedup_only | 3 | trend_only_ci_crosses_zero |
| wikitext2_paper | hdqspp | 3 | trend_only_ci_crosses_zero |
| wikitext2_paper | hdqspp_v2 | 3 | trend_only_ci_crosses_zero |
| wikitext2_paper | hdqspp_v2_no_token_frequency | 3 | trend_only_ci_crosses_zero |
| wikitext2_paper | hdqspp_v3 | 3 | trend_only_ci_crosses_zero |
| wikitext2_paper | length_filter | 3 | negative_preliminary_trend |
| wikitext2_paper | random_same_keep_rate | 3 | trend_only_ci_crosses_zero |
