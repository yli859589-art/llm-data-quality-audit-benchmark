# Run All Checks Report

- Status: `passed`
- Overall passed: `True`
- Started at: `2026-06-15T18:10:21+00:00`
- Finished at: `2026-06-15T18:15:11+00:00`
- Duration seconds: `289.770`
- Failed groups: `none`
- Timeout groups: `none`
- Skipped groups: `level3_execution_checks, localmax_execution_checks, localmax_v2_execution_checks, localmax_v2_release_checks, localmax_ccfc_artifact_checks`

| Group | Required | Status | Return Code | Duration Seconds |
|---|---:|---|---:|---:|
| `legacy_core_tests` | `True` | `passed` | 0 | 37.245 |
| `step2_data_tests` | `True` | `passed` | 0 | 6.826 |
| `step3_tokenizer_tests` | `True` | `passed` | 0 | 7.173 |
| `step4_filter_tests` | `True` | `passed` | 0 | 1.639 |
| `step5_training_tests` | `True` | `passed` | 0 | 15.990 |
| `step6_urd_tests` | `True` | `passed` | 0 | 8.547 |
| `step7_evaluation_tests` | `True` | `passed` | 0 | 12.859 |
| `step8_mechanism_tests` | `True` | `passed` | 0 | 2.172 |
| `step9_readiness_tests` | `True` | `passed` | 0 | 69.515 |
| `step10A_protocol_tests` | `True` | `passed` | 0 | 15.357 |
| `step10B_execution_tests` | `True` | `passed` | 0 | 1.433 |
| `step10B_localmax_tests` | `True` | `passed` | 0 | 1.956 |
| `step10C_localmax_release_tests` | `True` | `passed` | 0 | 23.444 |
| `localmax_v2_tests` | `True` | `passed` | 0 | 1.692 |
| `localmax_ccfc_tests` | `True` | `passed` | 0 | 0.861 |
| `manifest_checks` | `True` | `passed` | 0 | 4.894 |
| `artifact_checks` | `True` | `passed` | 0 | 5.647 |
| `claim_checks` | `True` | `passed` | 0 | 2.768 |
| `level3_gate_checks` | `True` | `passed` | 0 | 1.481 |
| `dataaudit_lm_checks` | `True` | `passed` | 0 | 13.299 |
| `localmax_release_checks` | `True` | `passed` | 0 | 51.387 |
| `registry_finalization_checks` | `True` | `passed` | 0 | 3.582 |

## Command Tails

### legacy_core_tests

- Command: `python -m pytest tests/test_algorithm_edges.py tests/test_clean_artifacts.py tests/test_data_quality_research.py tests/test_dataaudit_backup_restore_metadata.py tests/test_dataaudit_cluster_split.py tests/test_dataaudit_downstream_target_mask.py tests/test_dataaudit_exact_dedup.py tests/test_dataaudit_lm_metrics.py tests/test_dataaudit_lm_phase1.py tests/test_dataaudit_minhash_dedup.py tests/test_dataaudit_naming_scope.py tests/test_dataaudit_random_token_matched.py tests/test_dataaudit_raw_duplicate_retention.py tests/test_dataaudit_reference_lm_scoring.py tests/test_dataaudit_rehearsal.py tests/test_dataaudit_release_gate.py tests/test_dataaudit_training_initialization.py tests/test_dataaudit_training_sampling.py tests/test_dataset_matrix.py tests/test_datasets.py tests/test_experiment_infrastructure.py tests/test_hdqs_scoring.py tests/test_llm_benchmark.py tests/test_near_dedup.py tests/test_research_artifacts.py tests/test_smoke.py tests/test_statistics.py tests/test_supporting_edges.py -q`
- Status: `passed`

```text
........................................................................ [ 81%]
................                                                         [100%]
88 passed in 34.45s
```

### step2_data_tests

- Command: `python -m pytest tests/test_data_sources_step2.py tests/test_dataset_manifest_step2.py tests/test_token_budget_step2.py tests/test_prepare_data_v2_step2.py tests/test_no_fallback_step2.py -q`
- Status: `passed`

```text
.............                                                            [100%]
13 passed in 4.61s
```

### step3_tokenizer_tests

- Command: `python -m pytest tests/test_tokenization_step3.py tests/test_tokenizer_manifest_step3.py tests/test_tokenizer_budget_step3.py tests/test_train_tokenizer_v2_step3.py -q`
- Status: `passed`

```text
..........                                                               [100%]
10 passed in 4.36s
```

### step4_filter_tests

- Command: `python -m pytest tests/test_filters_v2_step4.py tests/test_filter_manifests_step4.py tests/test_run_filter_v2_step4.py tests/test_keep_rate_step4.py tests/test_proxy_filter_boundaries_step4.py -q`
- Status: `passed`

```text
.............                                                            [100%]
13 passed in 0.76s
```

### step5_training_tests

- Command: `python -m pytest tests/test_models_v2_step5.py tests/test_training_config_step5.py tests/test_training_data_adapter_step5.py tests/test_train_model_v2_step5.py tests/test_training_manifests_step5.py tests/test_training_no_main_results_pollution_step5.py -q`
- Status: `passed`

```text
.............                                                            [100%]
13 passed in 13.07s
```

### step6_urd_tests

- Command: `python -m pytest tests/test_urd_components_step6.py tests/test_urd_selector_step6.py tests/test_urd_pareto_step6.py tests/test_urd_ablation_step6.py tests/test_urd_manifest_step6.py tests/test_urd_no_main_results_pollution_step6.py -q`
- Status: `passed`

```text
........                                                                 [100%]
8 passed in 6.21s
```

### step7_evaluation_tests

- Command: `python -m pytest tests/test_evaluation_schema_step7.py tests/test_lm_metrics_step7.py tests/test_downstream_protocol_step7.py tests/test_risk_eval_step7.py tests/test_diversity_eval_step7.py tests/test_cost_eval_step7.py tests/test_stability_step7.py tests/test_pareto_eval_step7.py tests/test_evaluation_manifests_step7.py tests/test_evaluation_no_main_results_pollution_step7.py -q`
- Status: `passed`

```text
.............                                                            [100%]
13 passed in 10.64s
```

### step8_mechanism_tests

- Command: `python -m pytest tests/test_mechanism_schema_step8.py tests/test_proxy_utility_step8.py tests/test_overfiltering_step8.py tests/test_diversity_loss_step8.py tests/test_domain_shift_step8.py tests/test_rank_stability_step8.py tests/test_tokenizer_sensitivity_step8.py tests/test_scale_trend_step8.py tests/test_failure_taxonomy_step8.py tests/test_pareto_mechanism_step8.py tests/test_mechanism_manifests_step8.py tests/test_mechanism_no_main_results_pollution_step8.py -q`
- Status: `passed`

```text
..............                                                           [100%]
14 passed in 1.39s
```

### step9_readiness_tests

- Command: `python -m pytest tests/test_readiness_v2_step9.py tests/test_level3_gates_step9.py tests/test_artifact_registry_v2_step9.py tests/test_claim_map_step9.py tests/test_no_smoke_in_main_step9.py tests/test_no_protocol_as_completed_step9.py tests/test_no_level2_as_level3_step9.py tests/test_run_all_checks_step9.py tests/test_registry_to_tables_step9.py tests/test_step9_technical_debt_fixes.py tests/test_step9_level3_artifact_hygiene.py -q`
- Status: `passed`

```text
................................                                         [100%]
32 passed in 68.47s (0:01:08)
```

### step10A_protocol_tests

- Command: `python -m pytest tests/test_level3_protocol_step10A.py tests/test_level3_preflight_step10A.py tests/test_level3_artifact_paths_step10A.py tests/test_level3_claim_boundary_step10A.py tests/test_level3_dryrun_scripts_step10A.py tests/test_step10A_no_execution_pollution.py tests/test_artifact_scanner_path_independence_step10A.py tests/test_artifact_registry_finalization_step10A.py tests/test_step10A_hotfix_no_execution_pollution.py -q`
- Status: `passed`

```text
......................                                                   [100%]
22 passed in 14.28s
```

### step10B_execution_tests

- Command: `python -m pytest tests/test_step10B_environment.py tests/test_step10B_data_execution.py tests/test_step10B_tokenizer_execution.py tests/test_step10B_filter_execution.py tests/test_step10B_training_execution.py tests/test_step10B_evaluation_execution.py tests/test_step10B_mechanism_execution.py tests/test_step10B_registry_tables.py tests/test_step10B_readiness.py tests/test_step10B_no_false_level3_claims.py -q`
- Status: `passed`

```text
............                                                             [100%]
12 passed in 0.66s
```

### step10B_localmax_tests

- Command: `python -m pytest tests/test_localmax_execution_fix_step10B.py tests/test_localmax_minimal_data_threshold_step10B.py tests/test_localmax_minimal_training_outputs_step10B.py tests/test_localmax_nonempty_tables_step10B.py tests/test_localmax_no_fake_completion_step10B.py tests/test_localmax_training_strengthen_step10B.py tests/test_localmax_ppl_clipping_step10B.py tests/test_localmax_strengthened_tables_step10B.py tests/test_localmax_strengthened_readiness_step10B.py tests/test_localmax_strengthened_no_false_claims_step10B.py tests/test_localmax_environment_step10B.py tests/test_localmax_data_step10B.py tests/test_localmax_tokenizer_step10B.py tests/test_localmax_filters_step10B.py tests/test_localmax_training_step10B.py tests/test_localmax_evaluation_step10B.py tests/test_localmax_mechanism_step10B.py tests/test_localmax_registry_tables_step10B.py tests/test_localmax_readiness_step10B.py tests/test_localmax_no_false_level3_claims_step10B.py -q`
- Status: `passed`

```text
.........................                                                [100%]
25 passed in 1.22s
```

### step10C_localmax_release_tests

- Command: `python -m pytest tests/test_localmax_release_step10C.py tests/test_localmax_claim_boundary_step10C.py tests/test_localmax_release_registry_step10C.py tests/test_localmax_readme_resume_step10C.py tests/test_localmax_no_false_level3_claims_step10C.py tests/test_localmax_release_figures_step10C.py tests/test_localmax_release_figure_readability_step10C_hotfix.py tests/test_localmax_release_cross_platform_hashes_step10C_hotfix.py tests/test_localmax_release_idempotency_step10C_hotfix.py tests/test_localmax_release_canonical_io_step10C_hotfix.py tests/test_localmax_release_bundle_scope_step10C_hotfix.py tests/test_localmax_release_bundle_links_step10C_hotfix.py tests/test_localmax_release_no_result_modification_step10C_hotfix.py -q`
- Status: `passed`

```text
...........................                                              [100%]
27 passed in 22.42s
```

### localmax_v2_tests

- Command: `python -m pytest tests/test_localmax_v2_metric_audit.py tests/test_localmax_v2_data_scale.py tests/test_localmax_v2_filter_execution.py tests/test_localmax_v2_training_budget.py tests/test_localmax_v2_evaluation.py tests/test_localmax_v2_statistics.py tests/test_localmax_v2_mechanism.py tests/test_localmax_v2_tables.py tests/test_localmax_v2_readiness.py tests/test_localmax_v2_claim_boundary.py tests/test_localmax_v2_registry_truthfulness.py tests/test_localmax_v2_bundle_integrity.py tests/test_localmax_v2_no_historical_pollution.py -q`
- Status: `passed`

```text
.............                                                            [100%]
13 passed in 0.93s
```

### localmax_ccfc_tests

- Command: `python -m pytest tests/test_localmax_ccfc_strengthening.py -q`
- Status: `passed`

```text
....                                                                     [100%]
4 passed in 0.09s
```

### manifest_checks

- Command: `python scripts/check_filter_manifests.py --include-step4 ; python scripts/check_training_manifests.py --include-step5 ; python scripts/check_urd_manifests.py --include-step6 ; python scripts/check_evaluation_manifests.py --include-step7 ; python scripts/check_mechanism_manifests.py --include-step8`
- Status: `passed`

```text
Filter manifest check: ok (8 manifests)
Training manifest check: ok (1 manifests)
URD manifest check: ok (3 manifests)
Evaluation manifest check: ok (7 manifests)
Mechanism manifest check: ok (9 manifests)
```

### artifact_checks

- Command: `python scripts/check_repo.py --clean ; python scripts/capture_environment.py ; python scripts/check_registry_schema.py ; python scripts/check_artifact_lineage.py ; python scripts/check_main_results_purity.py`
- Status: `passed`

```text
Artifact check: ok
Repository cleanup removed 0 generated cache/temp paths.
Repository hygiene check: ok
Environment fingerprint: 12251c423367c2d5f70fbc2023dc58a04172a3d94c11598c289660d18176d099
Artifact: artifacts\environment\fingerprint.json
Registry schema check: ok (153 rows)
Artifact lineage check: ok (153 rows, 42 superseded)
Main results purity check: ok (24 rows)
```

### claim_checks

- Command: `python scripts/check_claims_supported.py ; python scripts/check_claim_hygiene.py ; python scripts/check_claim_map.py ; python scripts/check_no_forbidden_claims.py ; python scripts/check_no_smoke_in_main.py ; python scripts/check_no_protocol_as_completed.py ; python scripts/check_no_level2_as_level3.py`
- Status: `passed`

```text
Claim support check: ok
Claim hygiene: passed
Report: artifacts/release/claim_hygiene_report.json
Claim map check: ok
Forbidden claim check: ok
No-smoke-in-main check: ok
No-protocol-as-completed check: ok
No-Level2-as-Level3 check: ok
```

### level3_gate_checks

- Command: `python scripts/check_level3_gates.py ; python scripts/check_level3_protocol.py ; python scripts/check_level3_preflight.py ; python scripts/write_step10A_readiness_report.py`
- Status: `passed`

```text
Level 3 gates checked:
- data_gate: not_ready
- tokenizer_gate: partial
- filter_gate: partial
- model_scale_gate: partial
- evaluation_gate: partial
- mechanism_gate: partial
- claim_gate: pass
Overall readiness: LEVEL3_PIPELINE_READY
Level 3 protocol check: ok
Level 3 preflight check: ok
Step 10A readiness report: completed
Report: artifacts/reports/step10A_readiness_report.json
```

### dataaudit_lm_checks

- Command: `python scripts/dataaudit_lm/audit_metric_correctness.py ; python scripts/dataaudit_lm/audit_experiment_fairness.py ; python scripts/dataaudit_lm/verify_artifacts.py ; python scripts/dataaudit_lm/write_migration_and_protocol_reports.py ; python scripts/dataaudit_lm/run_rehearsal.py ; python scripts/dataaudit_lm/finalize_release.py --audit-only ; python scripts/dataaudit_lm/verify_document_consistency.py ; python scripts/dataaudit_lm/verify_fresh_clone.py --light ; python scripts/dataaudit_lm/generate_naming_inventory.py`
- Status: `passed`

```text
{"metric_audit_passed": true, "status": "METRIC_AUDIT_PASSED"}
{"fairness_metadata_checked": true, "final_matrix_complete": false}
{"artifact_integrity_verified": true, "missing": []}
{"migration_rows": 14, "freeze_status": "frozen_for_rehearsal_only"}
{"rehearsal_passed": true, "methods": 8}
{"status": "MULTI_SEED_TRAINING_COMPLETED", "mode": "audit-only", "final_release_gate_passed": false, "message": "AUDIT_COMPLETED_RELEASE_NOT_READY"}
{"document_consistency_verified": true, "forbidden_terms": [], "missing_numbers": []}
{"fresh_clone_verified": true, "light": true}
{"new_scope_hit_count": 0, "full_repo_hit_count": 2399}
```

### localmax_release_checks

- Command: `python scripts/localmax/make_localmax_release_tables.py ; python scripts/localmax/make_localmax_release_figures.py ; python scripts/localmax/check_localmax_release_claims.py ; python scripts/localmax/check_localmax_release_bundle.py ; python scripts/localmax/check_localmax_release_idempotency.py ; python scripts/localmax/finalize_localmax_release.py ; python scripts/localmax/check_localmax_release_claims.py ; python scripts/localmax/check_localmax_release_bundle.py`
- Status: `passed`

```text
{"localmax_release_tables_ready": true, "main_release_rows": 24}
{"localmax_release_figures_ready": true, "figures": 12}
LocalMax release claim check: ok
LocalMax release bundle check: ok
LocalMax release claim check: ok
LocalMax release claim check: ok
{"blocking_failures": [], "current_readiness": "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED", "release_manifest": "artifacts/localmax_release/localmax_release_manifest.json", "release_registry": "artifacts/localmax_release/localmax_artifact_registry.jsonl", "status": "completed", "step10C_localmax_release_ready": true, "step_report": "artifacts/reports/step10C_localmax_release_report.json"}
{"blocking_failures": [], "current_readiness": "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED", "release_manifest": "artifacts/localmax_release/localmax_release_manifest.json", "release_registry": "artifacts/localmax_release/localmax_artifact_registry.jsonl", "status": "completed", "step10C_localmax_release_ready": true, "step_report": "artifacts/reports/step10C_localmax_release_report.json"}
LocalMax release idempotency check: ok
{"blocking_failures": [], "current_readiness": "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED", "release_manifest": "artifacts/localmax_release/localmax_release_manifest.json", "release_registry": "artifacts/localmax_release/localmax_artifact_registry.jsonl", "status": "completed", "step10C_localmax_release_ready": true, "step_report": "artifacts/reports/step10C_localmax_release_report.json"}
LocalMax release claim check: ok
LocalMax release bundle check: ok
```

### registry_finalization_checks

- Command: `python scripts/finalize_artifact_registry_v2.py ; python scripts/check_registry_to_tables.py ; python scripts/check_main_results_from_registry.py`
- Status: `passed`

```text
Artifact registry v2 finalized: 832 records
Artifact registry hash check after finalization: ok
Registry-to-table consistency check: ok (3 main table records)
Main-results-from-registry check: ok
```

