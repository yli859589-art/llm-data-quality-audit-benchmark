# HDQS++ Freezing Report

No test leakage: the test split was not used for threshold, weight, or baseline selection.
- Dataset: `wikitext2_paper`
- Dataset scope: `official_split`
- Selection split: `dev`
- Dev metric: `final_val_perplexity`
- Candidate weights: `{'lexical_diversity': 1.0, 'char_entropy': 1.0, 'token_entropy': 0.8, 'repetition_penalty': 1.3, 'ngram_repetition_penalty': 1.0, 'pii_density_penalty': 1.2, 'url_html_noise_penalty': 1.0, 'non_linguistic_symbol_penalty': 1.0, 'length_prior': 0.8, 'language_consistency': 0.7, 'optional_lm_surprisal': 0.0, 'duplicate_cluster_penalty': 0.0}`
- Selected weights: `{'lexical_diversity': 1.0, 'char_entropy': 1.0, 'token_entropy': 0.8, 'repetition_penalty': 1.3, 'ngram_repetition_penalty': 1.0, 'pii_density_penalty': 1.2, 'url_html_noise_penalty': 1.0, 'non_linguistic_symbol_penalty': 1.0, 'length_prior': 0.8, 'language_consistency': 0.7, 'optional_lm_surprisal': 0.0, 'duplicate_cluster_penalty': 0.0}`
- Config hash: `bcd0c29660def43181203c91edab893daf6e4a899201105008e843cdcc28657e`
- Source run IDs: `train:wikitext2_paper:small:raw:1:completed_training:2026-06-04T08:30:31+00:00, train:wikitext2_paper:small:hdqspp:1:completed_training:2026-06-04T08:33:29+00:00, train:wikitext2_paper:small:raw:2:completed_training:2026-06-04T08:34:11+00:00, train:wikitext2_paper:small:hdqspp:2:completed_training:2026-06-04T08:36:50+00:00, train:wikitext2_paper:small:raw:3:completed_training:2026-06-04T08:37:19+00:00, train:wikitext2_paper:small:hdqspp:3:completed_training:2026-06-04T08:39:33+00:00`
- Tokenizer hash: `1ea189d583a09abd7baad7a9d2fd15c6800e31c1740d05f3a604f140adc2d84d`
- Vocab size: `283`
- Evaluated validation tokens: `53248`
- Test split was not used for selection: `true`
