# Data Intervention Ablation Table

| Variant | Documents | Characters | Duplicate rate | PII-like hits | Mean HDQS |
| --- | ---: | ---: | ---: | ---: | ---: |
| `raw_noisy_baseline` | 93 | 36747 | 0.226 | 39 | 0.847 |
| `clean_only` | 93 | 34445 | 0.226 | 39 | 0.892 |
| `pii_redact_only` | 93 | 36413 | 0.226 | 0 | 0.845 |
| `exact_dedup_only` | 72 | 29315 | 0.000 | 33 | 0.861 |
| `near_dedup_only` | 62 | 25100 | 0.000 | 27 | 0.869 |
| `rule_filter_only` | 80 | 33416 | 0.150 | 39 | 0.870 |
| `perplexity_filter_proxy` | 52 | 20664 | 0.154 | 21 | 0.915 |
| `hdqs_filter` | 60 | 24022 | 0.133 | 24 | 0.901 |
| `full_without_hdqs` | 60 | 22838 | 0.000 | 0 | 0.912 |
| `full_pipeline` | 56 | 21064 | 0.000 | 0 | 0.922 |
