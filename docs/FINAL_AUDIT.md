# Final Audit

Date: 2026-06-04

1. Current readiness: `EXPERIMENT-CANDIDATE`.
2. Method status: `honest_audit_framework`.
3. `ccf_c_ready`: `false`.
4. v2 failed because distribution diagnostics improved while validation PPL worsened.
5. Promising v2 ablation: `ablation_v2_without_token_frequency_preservation`.
6. Stage 2.6 selected promising variants via `scripts/select_promising_variants.py`.
7. HDQS++ v3 was implemented and frozen from dev-only evidence.
8. v3 removed token-frequency preservation, weakened length/distribution constraints, and added calibrated soft selection.
9. v3 3-seed completion: `True`.
10. v3 vs raw raw-minus-v3 diff: `-0.6126`.
11. v3 vs random/dedup/v1/v2: see `artifacts/stats/method_comparison_summary.csv`.
12. Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`.
13. Audit/diagnostics framework repositioned: `true`.
14. `main_results` is generated from completed-training registry rows only.
15. `method_debug` remains isolated.
16. filtering-only artifacts remain isolated.
17. run registry is append-oriented; superseded artifact hashes are handled by lineage checks.
18. split integrity and no-test-leakage checks are required final gates.
19. Current project value: The project demonstrates a reproducible data-quality risk audit loop: real data, fair baselines, frozen configs, registry lineage, diagnostics, ablations, and claim-safety reporting.
20. Current shortfall: The method claim remains limited by 3 seeds, small model scale, streaming-sample scope for OpenWebText/C4, and the fact that filtering does not outperform raw.
21. Next phase should expand datasets after this honest method boundary is accepted.
