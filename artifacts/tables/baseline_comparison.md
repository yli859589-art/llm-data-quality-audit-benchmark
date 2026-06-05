# Baseline Comparison

Mode: smoke/dev registry consolidation
Seed setting: recorded per row
Training budget: data-filter-only rows do not train a model
Interpretation: supports engineering readiness, not paper-level model claims

| Dataset | Baseline | Seed | Retention | Fallback | Status |
|---|---|---:|---:|---|---|
| wikitext2_smoke | raw | 13 | 1.000 | real_nonfallback | completed_filtering_only |
| wikitext2_smoke | random_same_keep_rate | 13 | 0.600 | real_nonfallback | completed_filtering_only |
| wikitext2_smoke | length_filter | 13 | 0.600 | real_nonfallback | completed_filtering_only |
| wikitext2_smoke | c4_gopher_heuristic | 13 | 0.600 | real_nonfallback | completed_filtering_only |
| wikitext2_smoke | dedup_only | 13 | 0.333 | real_nonfallback | completed_filtering_only |
| wikitext2_smoke | perplexity_quality_ngram | 13 | 0.600 | real_nonfallback | completed_filtering_only |
| wikitext2_smoke | independent_quality_score | 13 | 0.600 | real_nonfallback | completed_filtering_only |
| wikitext2_smoke | optional_external_wrapper | 13 | 0.000 | real_nonfallback | incomplete |
| openwebtext_smoke | raw | 13 | 1.000 | real_nonfallback | completed_filtering_only |
| openwebtext_smoke | random_same_keep_rate | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| openwebtext_smoke | length_filter | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| openwebtext_smoke | c4_gopher_heuristic | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| openwebtext_smoke | dedup_only | 13 | 0.500 | real_nonfallback | completed_filtering_only |
| openwebtext_smoke | perplexity_quality_ngram | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| openwebtext_smoke | independent_quality_score | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| openwebtext_smoke | optional_external_wrapper | 13 | 0.000 | real_nonfallback | incomplete |
| c4_en_smoke | raw | 13 | 1.000 | real_nonfallback | completed_filtering_only |
| c4_en_smoke | random_same_keep_rate | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| c4_en_smoke | length_filter | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| c4_en_smoke | c4_gopher_heuristic | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| c4_en_smoke | dedup_only | 13 | 0.500 | real_nonfallback | completed_filtering_only |
| c4_en_smoke | perplexity_quality_ngram | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| c4_en_smoke | independent_quality_score | 13 | 0.636 | real_nonfallback | completed_filtering_only |
| c4_en_smoke | optional_external_wrapper | 13 | 0.000 | real_nonfallback | incomplete |
| wikitext2_paper | data_prepare | 13 | 1.000 | real_nonfallback | completed_filtering_only |
| wikitext2_paper | raw | 13 | 1.000 | real_nonfallback | completed_training |
| wikitext2_paper | hdqspp | 13 | 0.600 | real_nonfallback | completed_training |
| wikitext2_paper | data_prepare | 13 | 1.000 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | raw | 13 | 1.000 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | random_same_keep_rate | 13 | 0.601 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | length_filter | 13 | 0.601 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | dedup_only | 13 | 0.993 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | hdqspp | 13 | 0.601 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | raw | 1 | 1.000 | real_local_nonfallback | completed_training |
| wikitext2_paper | random_same_keep_rate | 1 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | length_filter | 1 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | dedup_only | 1 | 0.992 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp | 1 | 0.601 | real_local_nonfallback | completed_training |
| wikitext2_paper | raw | 2 | 1.000 | real_local_nonfallback | completed_training |
| wikitext2_paper | random_same_keep_rate | 2 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | length_filter | 2 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | dedup_only | 2 | 0.992 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp | 2 | 0.601 | real_local_nonfallback | completed_training |
| wikitext2_paper | raw | 3 | 1.000 | real_local_nonfallback | completed_training |
| wikitext2_paper | random_same_keep_rate | 3 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | length_filter | 3 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | dedup_only | 3 | 0.992 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp | 3 | 0.601 | real_local_nonfallback | completed_training |
| wikitext2_paper | data_prepare | 13 | 1.000 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | method_debug | 13 | 0.000 | real_local_nonfallback | lightweight_dev |
| wikitext2_paper | freeze_hdqspp_v2 |  | 0.000 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | raw | 13 | 1.000 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | random_same_keep_rate | 13 | 0.601 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | length_filter | 13 | 0.601 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | dedup_only | 13 | 0.993 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | hdqspp | 13 | 0.601 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | hdqspp_v2 | 13 | 0.851 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | raw | 1 | 1.000 | real_local_nonfallback | completed_training |
| wikitext2_paper | random_same_keep_rate | 1 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | length_filter | 1 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | dedup_only | 1 | 0.992 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp | 1 | 0.601 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp_v2 | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | raw | 2 | 1.000 | real_local_nonfallback | completed_training |
| wikitext2_paper | random_same_keep_rate | 2 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | length_filter | 2 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | dedup_only | 2 | 0.992 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp | 2 | 0.601 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp_v2 | 2 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | raw | 3 | 1.000 | real_local_nonfallback | completed_training |
| wikitext2_paper | random_same_keep_rate | 3 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | length_filter | 3 | 0.599 | real_local_nonfallback | completed_training |
| wikitext2_paper | dedup_only | 3 | 0.992 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp | 3 | 0.601 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp_v2 | 3 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v2_full | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v2_without_length_prior | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v2_without_distribution_preservation | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v2_without_token_frequency_preservation | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v2_without_repetition_penalty | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v2_without_quality_diversity_balance |  | 0.000 | real_local_nonfallback | configured_not_run |
| wikitext2_paper | ablation_v2_hard_filtering |  | 0.000 | real_local_nonfallback | configured_not_run |
| wikitext2_paper | ablation_v2_soft_weighting_curriculum |  | 0.000 | real_local_nonfallback | configured_not_run |
| wikitext2_paper | freeze_hdqspp_v3 |  | 0.000 | real_local_nonfallback | completed_filtering_only |
| wikitext2_paper | hdqspp_v2_no_token_frequency | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp_v2_no_token_frequency | 2 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp_v2_no_token_frequency | 3 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp_v3 | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp_v3 | 2 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | hdqspp_v3 | 3 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v3_full | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v3_without_soft_weighting | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v3_without_keep_rate_calibration | 1 | 0.601 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v3_without_quality_diversity_balance | 1 | 0.851 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v3_hard_filtering_only | 1 | 0.601 | real_local_nonfallback | completed_training |
| wikitext2_paper | ablation_v3_soft_weighting_only |  | 0.000 | real_local_nonfallback | configured_not_run |
| wikitext2_paper | ablation_v3_without_length_guardrails |  | 0.000 | real_local_nonfallback | configured_not_run |
| wikitext2_paper | ablation_v3_without_repetition_penalty |  | 0.000 | real_local_nonfallback | configured_not_run |
| wikitext2_paper | freeze_hdqspp_v3 |  | 0.000 | real_local_nonfallback | completed_filtering_only |
| openwebtext_streaming | data_prepare | 31 | 0.000 | failed_due_to_environment | failed_due_to_environment |
| openwebtext_streaming | data_prepare | 31 | 0.000 | failed_due_to_environment | failed_due_to_environment |
| openwebtext_streaming | data_prepare | 31 | 1.000 | real_nonfallback | completed_filtering_only |
| c4_en_streaming | data_prepare | 37 | 1.000 | real_nonfallback | completed_filtering_only |
| openwebtext_streaming | raw | 1 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | random_same_keep_rate | 1 | 0.602 | real_nonfallback | completed_training |
| openwebtext_streaming | dedup_only | 1 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | hdqspp_v3 | 1 | 0.860 | real_nonfallback | completed_training |
| openwebtext_streaming | raw | 2 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | random_same_keep_rate | 2 | 0.602 | real_nonfallback | completed_training |
| openwebtext_streaming | dedup_only | 2 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | hdqspp_v3 | 2 | 0.860 | real_nonfallback | completed_training |
| openwebtext_streaming | raw | 3 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | random_same_keep_rate | 3 | 0.602 | real_nonfallback | completed_training |
| openwebtext_streaming | dedup_only | 3 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | hdqspp_v3 | 3 | 0.860 | real_nonfallback | completed_training |
| c4_en_streaming | raw | 1 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | random_same_keep_rate | 1 | 0.599 | real_nonfallback | completed_training |
| c4_en_streaming | dedup_only | 1 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | hdqspp_v3 | 1 | 0.853 | real_nonfallback | completed_training |
| c4_en_streaming | raw | 2 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | random_same_keep_rate | 2 | 0.599 | real_nonfallback | completed_training |
| c4_en_streaming | dedup_only | 2 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | hdqspp_v3 | 2 | 0.853 | real_nonfallback | completed_training |
| c4_en_streaming | raw | 3 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | random_same_keep_rate | 3 | 0.599 | real_nonfallback | completed_training |
| c4_en_streaming | dedup_only | 3 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | hdqspp_v3 | 3 | 0.853 | real_nonfallback | completed_training |
| openwebtext_streaming | data_prepare | 31 | 1.000 | real_nonfallback | completed_filtering_only |
| c4_en_streaming | data_prepare | 37 | 1.000 | real_nonfallback | completed_filtering_only |
| openwebtext_streaming | raw | 1 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | random_same_keep_rate | 1 | 0.602 | real_nonfallback | completed_training |
| openwebtext_streaming | dedup_only | 1 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | hdqspp_v3 | 1 | 0.860 | real_nonfallback | completed_training |
| openwebtext_streaming | raw | 2 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | random_same_keep_rate | 2 | 0.602 | real_nonfallback | completed_training |
| openwebtext_streaming | dedup_only | 2 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | hdqspp_v3 | 2 | 0.860 | real_nonfallback | completed_training |
| openwebtext_streaming | raw | 3 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | random_same_keep_rate | 3 | 0.602 | real_nonfallback | completed_training |
| openwebtext_streaming | dedup_only | 3 | 1.000 | real_nonfallback | completed_training |
| openwebtext_streaming | hdqspp_v3 | 3 | 0.860 | real_nonfallback | completed_training |
| c4_en_streaming | raw | 1 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | random_same_keep_rate | 1 | 0.599 | real_nonfallback | completed_training |
| c4_en_streaming | dedup_only | 1 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | hdqspp_v3 | 1 | 0.853 | real_nonfallback | completed_training |
| c4_en_streaming | raw | 2 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | random_same_keep_rate | 2 | 0.599 | real_nonfallback | completed_training |
| c4_en_streaming | dedup_only | 2 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | hdqspp_v3 | 2 | 0.853 | real_nonfallback | completed_training |
| c4_en_streaming | raw | 3 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | random_same_keep_rate | 3 | 0.599 | real_nonfallback | completed_training |
| c4_en_streaming | dedup_only | 3 | 1.000 | real_nonfallback | completed_training |
| c4_en_streaming | hdqspp_v3 | 3 | 0.853 | real_nonfallback | completed_training |
