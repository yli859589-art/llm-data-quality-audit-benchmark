# Baseline Comparison

Mode: smoke/dev registry consolidation
Seed setting: recorded per row
Training budget: data-filter-only rows do not train a model
Interpretation: supports engineering readiness, not paper-level model claims

| Dataset | Baseline | Seed | Retention | Fallback | Status |
|---|---|---:|---:|---|---|
| wikitext2_smoke | raw | 13 | 1.000 | True | data_filter_only |
| wikitext2_smoke | random_same_keep_rate | 13 | 0.600 | True | data_filter_only |
| wikitext2_smoke | length_filter | 13 | 0.600 | True | data_filter_only |
| wikitext2_smoke | c4_gopher_heuristic | 13 | 0.600 | True | data_filter_only |
| wikitext2_smoke | dedup_only | 13 | 0.333 | True | data_filter_only |
| wikitext2_smoke | perplexity_quality_ngram | 13 | 0.600 | True | data_filter_only |
| wikitext2_smoke | independent_quality_score | 13 | 0.600 | True | data_filter_only |
| wikitext2_smoke | optional_external_wrapper | 13 | 0.000 | True | skipped |
| openwebtext_smoke | raw | 13 | 1.000 | True | data_filter_only |
| openwebtext_smoke | random_same_keep_rate | 13 | 0.636 | True | data_filter_only |
| openwebtext_smoke | length_filter | 13 | 0.636 | True | data_filter_only |
| openwebtext_smoke | c4_gopher_heuristic | 13 | 0.636 | True | data_filter_only |
| openwebtext_smoke | dedup_only | 13 | 0.500 | True | data_filter_only |
| openwebtext_smoke | perplexity_quality_ngram | 13 | 0.636 | True | data_filter_only |
| openwebtext_smoke | independent_quality_score | 13 | 0.636 | True | data_filter_only |
| openwebtext_smoke | optional_external_wrapper | 13 | 0.000 | True | skipped |
| c4_en_smoke | raw | 13 | 1.000 | True | data_filter_only |
| c4_en_smoke | random_same_keep_rate | 13 | 0.636 | True | data_filter_only |
| c4_en_smoke | length_filter | 13 | 0.636 | True | data_filter_only |
| c4_en_smoke | c4_gopher_heuristic | 13 | 0.636 | True | data_filter_only |
| c4_en_smoke | dedup_only | 13 | 0.500 | True | data_filter_only |
| c4_en_smoke | perplexity_quality_ngram | 13 | 0.636 | True | data_filter_only |
| c4_en_smoke | independent_quality_score | 13 | 0.636 | True | data_filter_only |
| c4_en_smoke | optional_external_wrapper | 13 | 0.000 | True | skipped |
