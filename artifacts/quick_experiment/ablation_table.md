# Data Intervention Ablation Table

| Variant | Documents | Characters | Duplicate rate | PII-like hits | Mean HDQS |
| --- | ---: | ---: | ---: | ---: | ---: |
| `raw_noisy_baseline` | 93 | 36747 | 0.226 | 39 | 0.833 |
| `clean_only` | 93 | 34445 | 0.226 | 39 | 0.869 |
| `pii_redact_only` | 93 | 36413 | 0.226 | 0 | 0.831 |
| `exact_dedup_only` | 72 | 29315 | 0.000 | 33 | 0.856 |
| `near_dedup_only` | 62 | 25100 | 0.000 | 27 | 0.865 |
| `jaccard_near_dedup_only` | 62 | 25100 | 0.000 | 27 | 0.865 |
| `rule_filter_only` | 80 | 33416 | 0.150 | 39 | 0.870 |
| `rule_quality_filter` | 80 | 33416 | 0.150 | 39 | 0.870 |
| `perplexity_filter_proxy` | 52 | 20664 | 0.154 | 21 | 0.907 |
| `proxy_perplexity_filter` | 52 | 20664 | 0.154 | 21 | 0.907 |
| `hdqs_filter` | 73 | 29575 | 0.151 | 24 | 0.880 |
| `hdqs_curriculum` | 73 | 29575 | 0.151 | 24 | 0.880 |
| `full_pipeline_without_clean` | 57 | 22813 | 0.000 | 0 | 0.875 |
| `full_pipeline_without_redact` | 60 | 23070 | 0.000 | 27 | 0.913 |
| `full_pipeline_without_exact_dedup` | 57 | 21492 | 0.000 | 0 | 0.910 |
| `full_pipeline_without_near_dedup` | 64 | 24151 | 0.000 | 0 | 0.909 |
| `full_without_hdqs` | 60 | 22838 | 0.000 | 0 | 0.904 |
| `full_pipeline` | 57 | 21492 | 0.000 | 0 | 0.910 |
| `minhash_lsh_near_dedup_only` | 62 | 25100 | 0.000 | 27 | 0.865 |
| `random_retention_matched_baseline` | 57 | 22943 | 0.211 | 33 | 0.830 |
| `length_matched_baseline` | 57 | 25083 | 0.158 | 39 | 0.848 |
| `quality_retention_matched_baseline` | 57 | 22768 | 0.140 | 24 | 0.900 |
