# LocalMax V2 Results

Status: `LOCAL_MAX_V2_STRONG_EVIDENCE_RELEASED`

Data scale: `200006900` GPT-2 tokens across two non-fallback datasets.

Training: 24/24 core runs completed; total training tokens_seen across method/seed runs: `24035328`.

Main metric: `valid_nll_nats_per_token`.

Best method per dataset by valid NLL: `{'c4_en_v2_100m': 'length_filter', 'openwebtext_v2_100m': 'length_filter'}`.

URD vs raw: `{'c4_en_v2_100m': {'ci_crosses_zero': True, 'improvement_claim_allowed': False, 'mean_paired_nll_improvement': 0.0009607486426830292, 'urd_mean_lower_than_raw': True}, 'openwebtext_v2_100m': {'ci_crosses_zero': True, 'improvement_claim_allowed': False, 'mean_paired_nll_improvement': -0.022342214981714886, 'urd_mean_lower_than_raw': False}}`.
