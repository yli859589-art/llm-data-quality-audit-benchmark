# Data Intervention Ablation Table

| Variant | Documents | Characters | Duplicate rate | PII-like hits | Mean HDQS |
| --- | ---: | ---: | ---: | ---: | ---: |
| `raw_noisy_baseline` | 102 | 44360 | 0.275 | 39 | 0.808 |
| `clean_only` | 102 | 41932 | 0.275 | 39 | 0.849 |
| `pii_redact_only` | 102 | 44026 | 0.275 | 0 | 0.807 |
| `exact_dedup_only` | 74 | 33906 | 0.000 | 33 | 0.843 |
| `near_dedup_only` | 64 | 29275 | 0.000 | 27 | 0.850 |
| `jaccard_near_dedup_only` | 64 | 29275 | 0.000 | 27 | 0.850 |
| `rule_filter_only` | 80 | 37726 | 0.150 | 39 | 0.865 |
| `rule_quality_filter` | 80 | 37726 | 0.150 | 39 | 0.865 |
| `perplexity_filter_proxy` | 44 | 20291 | 0.159 | 18 | 0.912 |
| `proxy_perplexity_filter` | 44 | 20291 | 0.159 | 18 | 0.912 |
| `hdqs_filter` | 72 | 33263 | 0.153 | 21 | 0.875 |
| `hdqs_curriculum` | 72 | 33263 | 0.153 | 21 | 0.875 |
| `full_pipeline_without_clean` | 58 | 26664 | 0.000 | 0 | 0.868 |
| `full_pipeline_without_redact` | 60 | 26411 | 0.000 | 27 | 0.918 |
| `full_pipeline_without_exact_dedup` | 58 | 25108 | 0.000 | 0 | 0.912 |
| `full_pipeline_without_near_dedup` | 65 | 28169 | 0.000 | 0 | 0.911 |
| `full_without_hdqs` | 60 | 26179 | 0.000 | 0 | 0.908 |
| `full_pipeline` | 58 | 25108 | 0.000 | 0 | 0.912 |
| `full_pipeline_without_hdqs` | 60 | 26179 | 0.000 | 0 | 0.908 |
| `minhash_lsh_near_dedup_only` | 64 | 29275 | 0.000 | 27 | 0.850 |
| `random_retention_matched_baseline` | 58 | 25648 | 0.276 | 24 | 0.801 |
| `length_matched_baseline` | 58 | 28797 | 0.155 | 39 | 0.856 |
| `quality_retention_matched_baseline` | 58 | 26703 | 0.138 | 21 | 0.891 |
