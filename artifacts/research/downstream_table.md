# Downstream Table

Mode: `quick` unless a table explicitly references paper-prototype.
Seed setting: `23` for quick artifacts; `23,42,3407` for multi-seed.
Training budget: `18000` characters per compared quick-mode variant.
Interpretation: generated evidence for reproducibility, diagnostics, and research-readiness inspection.
Limitation note: quick and paper-prototype results are preliminary; full multi-dataset, longer-budget runs are still required.

| variant | next_character_accuracy | held_out_perplexity | held_out_bits_per_character | held_out_noisy_robustness_proxy | simple_cloze_proxy_accuracy | toy_sentiment_proxy | small_classification_proxy | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_pipeline | 0.02734375 | 559217.5970602097 | 19.093050233562288 | 1.788212683679788e-06 | 0.02734375 | not_run_in_quick_mode | not_run_in_quick_mode | quick_trained_metric |
| hdqs_filter | 0.025390625 | 604081.1564385192 | 19.204382858633025 | 1.6554067104090767e-06 | 0.025390625 | not_run_in_quick_mode | not_run_in_quick_mode | quick_trained_metric |
| raw_noisy_baseline | 0.02734375 | 581636.8320220296 | 19.14975910492719 | 1.7192858927512433e-06 | 0.02734375 | not_run_in_quick_mode | not_run_in_quick_mode | quick_trained_metric |
| rule_filter_only | 0.02734375 | 610303.4309267955 | 19.219167175231796 | 1.6385292123975422e-06 | 0.02734375 | not_run_in_quick_mode | not_run_in_quick_mode | quick_trained_metric |
