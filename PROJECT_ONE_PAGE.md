# One Page Overview

LocalMax V2 evaluates data filtering for language-model pretraining under a fixed local budget: 2 datasets x 4 methods x 3 seeds, with 1M tokens_seen per run.

Best methods by valid NLL: `{'c4_en_v2_100m': 'length_filter', 'openwebtext_v2_100m': 'length_filter'}`.

URD-fixed evidence is reported honestly: `{'c4_en_v2_100m': {'ci_crosses_zero': True, 'improvement_claim_allowed': False, 'mean_paired_nll_improvement': 0.0009607486426830292, 'urd_mean_lower_than_raw': True}, 'openwebtext_v2_100m': {'ci_crosses_zero': True, 'improvement_claim_allowed': False, 'mean_paired_nll_improvement': -0.022342214981714886, 'urd_mean_lower_than_raw': False}}`.
