# Step 9 Hotfix Check Results

- Status: `passed`
- Overall passed: `True`
- Started at: `2026-06-11T12:14:20+00:00`
- Finished at: `2026-06-11T12:16:49+00:00`
- Duration seconds: `148.658`
- Failed commands: `0`
- Timeout commands: `0`

| Command | Status | Return Code | Duration Seconds |
|---|---|---:|---:|
| `python -m pytest tests/ -q` | `passed` | 0 | 58.763 |
| `python scripts/run_all_checks.py --timeout 300 --json-out artifacts/reports/run_all_checks_report.json --md-out artifacts/reports/run_all_checks_report.md` | `passed` | 0 | 80.138 |
| `python scripts/check_main_results_purity.py` | `passed` | 0 | 0.094 |
| `python scripts/check_claim_hygiene.py` | `passed` | 0 | 0.643 |
| `python scripts/check_claim_map.py` | `passed` | 0 | 0.100 |
| `python scripts/check_no_forbidden_claims.py` | `passed` | 0 | 0.194 |
| `python scripts/check_no_smoke_in_main.py` | `passed` | 0 | 0.102 |
| `python scripts/check_no_protocol_as_completed.py` | `passed` | 0 | 0.267 |
| `python scripts/check_no_level2_as_level3.py` | `passed` | 0 | 0.679 |
| `python scripts/check_level3_gates.py` | `passed` | 0 | 0.606 |
| `python scripts/check_registry_to_tables.py` | `passed` | 0 | 0.131 |
| `python scripts/check_main_results_from_registry.py` | `passed` | 0 | 0.125 |
| `python scripts/check_artifact_registry_v2.py` | `passed` | 0 | 0.235 |
| `python scripts/check_filter_manifests.py --include-step4` | `passed` | 0 | 0.305 |
| `python scripts/check_training_manifests.py --include-step5` | `passed` | 0 | 2.620 |
| `python scripts/check_urd_manifests.py --include-step6` | `passed` | 0 | 2.473 |
| `python scripts/check_evaluation_manifests.py --include-step7` | `passed` | 0 | 0.184 |
| `python scripts/check_mechanism_manifests.py --include-step8` | `passed` | 0 | 0.212 |
| `python scripts/write_step9_readiness_report.py` | `passed` | 0 | 0.567 |

## Output Tails

### `python -m pytest tests/ -q`

```text
........................................................................ [ 38%]
........................................................................ [ 77%]
.........................................                                [100%]
185 passed in 55.75s
```

### `python scripts/run_all_checks.py --timeout 300 --json-out artifacts/reports/run_all_checks_report.json --md-out artifacts/reports/run_all_checks_report.md`

```text
.py -q
.............                                                            [100%]
13 passed in 0.57s
OK python -m pytest tests/test_filters_v2_step4.py tests/test_filter_manifests_step4.py tests/test_run_filter_v2_step4.py tests/test_keep_rate_step4.py tests/test_proxy_filter_boundaries_step4.py -q
RUN python -m pytest tests/test_models_v2_step5.py tests/test_training_config_step5.py tests/test_training_data_adapter_step5.py tests/test_train_model_v2_step5.py tests/test_training_manifests_step5.py tests/test_training_no_main_results_pollution_step5.py -q
.............                                                            [100%]
13 passed in 12.82s
OK python -m pytest tests/test_models_v2_step5.py tests/test_training_config_step5.py tests/test_training_data_adapter_step5.py tests/test_train_model_v2_step5.py tests/test_training_manifests_step5.py tests/test_training_no_main_results_pollution_step5.py -q
RUN python -m pytest tests/test_urd_components_step6.py tests/test_urd_selector_step6.py tests/test_urd_pareto_step6.py tests/test_urd_ablation_step6.py tests/test_urd_manifest_step6.py tests/test_urd_no_main_results_pollution_step6.py -q
........                                                                 [100%]
8 passed in 5.37s
OK python -m pytest tests/test_urd_components_step6.py tests/test_urd_selector_step6.py tests/test_urd_pareto_step6.py tests/test_urd_ablation_step6.py tests/test_urd_manifest_step6.py tests/test_urd_no_main_results_pollution_step6.py -q
RUN python -m pytest tests/test_evaluation_schema_step7.py tests/test_lm_metrics_step7.py tests/test_downstream_protocol_step7.py tests/test_risk_eval_step7.py tests/test_diversity_eval_step7.py tests/test_cost_eval_step7.py tests/test_stability_step7.py tests/test_pareto_eval_step7.py tests/test_evaluation_manifests_step7.py tests/test_evaluation_no_main_results_pollution_step7.py -q
.............                                                            [100%]
13 passed in 0.97s
OK python -m pytest tests/test_evaluation_schema_step7.py tests/test_lm_metrics_step7.py tests/test_downstream_protocol_step7.py tests/test_risk_eval_step7.py tests/test_diversity_eval_step7.py tests/test_cost_eval_step7.py tests/test_stability_step7.py tests/test_pareto_eval_step7.py tests/test_evaluation_manifests_step7.py tests/test_evaluation_no_main_results_pollution_step7.py -q
RUN python -m pytest tests/test_mechanism_schema_step8.py tests/test_proxy_utility_step8.py tests/test_overfiltering_step8.py tests/test_diversity_loss_step8.py tests/test_domain_shift_step8.py tests/test_rank_stability_step8.py tests/test_tokenizer_sensitivity_step8.py tests/test_scale_trend_step8.py tests/test_failure_taxonomy_step8.py tests/test_pareto_mechanism_step8.py tests/test_mechanism_manifests_step8.py tests/test_mechanism_no_main_results_pollution_step8.py -q
..............                                                           [100%]
14 passed in 1.19s
OK python -m pytest tests/test_mechanism_schema_step8.py tests/test_proxy_utility_step8.py tests/test_overfiltering_step8.py tests/test_diversity_loss_step8.py tests/test_domain_shift_step8.py tests/test_rank_stability_step8.py tests/test_tokenizer_sensitivity_step8.py tests/test_scale_trend_step8.py tests/test_failure_taxonomy_step8.py tests/test_pareto_mechanism_step8.py tests/test_mechanism_manifests_step8.py tests/test_mechanism_no_main_results_pollution_step8.py -q
RUN python -m pytest tests/test_readiness_v2_step9.py tests/test_level3_gates_step9.py tests/test_artifact_registry_v2_step9.py tests/test_claim_map_step9.py tests/test_no_smoke_in_main_step9.py tests/test_no_protocol_as_completed_step9.py tests/test_no_level2_as_level3_step9.py tests/test_run_all_checks_step9.py tests/test_registry_to_tables_step9.py tests/test_step9_technical_debt_fixes.py tests/test_step9_level3_artifact_hygiene.py -q
................................                                         [100%]
32 passed in 6.62s
OK python -m pytest tests/test_readiness_v2_step9.py tests/test_level3_gates_step9.py tests/test_artifact_registry_v2_step9.py tests/test_claim_map_step9.py tests/test_no_smoke_in_main_step9.py tests/test_no_protocol_as_completed_step9.py tests/test_no_level2_as_level3_step9.py tests/test_run_all_checks_step9.py tests/test_registry_to_tables_step9.py tests/test_step9_technical_debt_fixes.py tests/test_step9_level3_artifact_hygiene.py -q
RUN python scripts/check_filter_manifests.py --include-step4
Filter manifest check: ok (8 manifests)
OK python scripts/check_filter_manifests.py --include-step4
RUN python scripts/check_training_manifests.py --include-step5
Training manifest check: ok (1 manifests)
OK python scripts/check_training_manifests.py --include-step5
RUN python scripts/check_urd_manifests.py --include-step6
URD manifest check: ok (3 manifests)
OK python scripts/check_urd_manifests.py --include-step6
RUN python scripts/check_evaluation_manifests.py --include-step7
Evaluation manifest check: ok (7 manifests)
OK python scripts/check_evaluation_manifests.py --include-step7
RUN python scripts/check_mechanism_manifests.py --include-step8
Mechanism manifest check: ok (9 manifests)
OK python scripts/check_mechanism_manifests.py --include-step8
RUN python scripts/check_repo.py --clean
Artifact check: ok
Repository cleanup removed 291 generated cache/temp paths.
Repository hygiene check: ok
OK python scripts/check_repo.py --clean
RUN python scripts/capture_environment.py
Environment fingerprint: 12251c423367c2d5f70fbc2023dc58a04172a3d94c11598c289660d18176d099
Artifact: artifacts\environment\fingerprint.json
OK python scripts/capture_environment.py
RUN python scripts/check_registry_schema.py
Registry schema check: ok (153 rows)
OK python scripts/check_registry_schema.py
RUN python scripts/check_artifact_lineage.py
Artifact lineage check: ok (153 rows, 42 superseded)
OK python scripts/check_artifact_lineage.py
RUN python scripts/check_main_results_purity.py
Main results purity check: ok (24 rows)
OK python scripts/check_main_results_purity.py
RUN python scripts/generate_artifact_registry_v2.py
Artifact registry v2 records: 143
Registry: artifacts/registry_v2/artifact_registry.jsonl
Summary: artifacts/registry_v2/artifact_registry_summary.json
Report: artifacts/reports/artifact_registry_v2_report.md
OK python scripts/generate_artifact_registry_v2.py
RUN python scripts/check_artifact_registry_v2.py
Artifact registry v2 check: ok (143 records)
OK python scripts/check_artifact_registry_v2.py
RUN python scripts/check_registry_to_tables.py
Registry-to-table consistency check: ok (3 main table records)
OK python scripts/check_registry_to_tables.py
RUN python scripts/check_main_results_from_registry.py
Main-results-from-registry check: ok
OK python scripts/check_main_results_from_registry.py
RUN python scripts/check_claims_supported.py
Claim support check: ok
OK python scripts/check_claims_supported.py
RUN python scripts/check_claim_hygiene.py
Claim hygiene: passed
Report: artifacts/release/claim_hygiene_report.json
OK python scripts/check_claim_hygiene.py
RUN python scripts/check_claim_map.py
Claim map check: ok
OK python scripts/check_claim_map.py
RUN python scripts/check_no_forbidden_claims.py
Forbidden claim check: ok
OK python scripts/check_no_forbidden_claims.py
RUN python scripts/check_no_smoke_in_main.py
No-smoke-in-main check: ok
OK python scripts/check_no_smoke_in_main.py
RUN python scripts/check_no_protocol_as_completed.py
No-protocol-as-completed check: ok
OK python scripts/check_no_protocol_as_completed.py
RUN python scripts/check_no_level2_as_level3.py
No-Level2-as-Level3 check: ok
OK python scripts/check_no_level2_as_level3.py
RUN python scripts/check_level3_gates.py
Level 3 gates checked:
- data_gate: not_ready
- tokenizer_gate: partial
- filter_gate: partial
- model_scale_gate: partial
- evaluation_gate: partial
- mechanism_gate: partial
- claim_gate: pass
Overall readiness: LEVEL3_PIPELINE_READY
OK python scripts/check_level3_gates.py
All checks passed.
```

### `python scripts/check_main_results_purity.py`

```text
Main results purity check: ok (24 rows)
```

### `python scripts/check_claim_hygiene.py`

```text
Claim hygiene: passed
Report: artifacts/release/claim_hygiene_report.json
```

### `python scripts/check_claim_map.py`

```text
Claim map check: ok
```

### `python scripts/check_no_forbidden_claims.py`

```text
Forbidden claim check: ok
```

### `python scripts/check_no_smoke_in_main.py`

```text
No-smoke-in-main check: ok
```

### `python scripts/check_no_protocol_as_completed.py`

```text
No-protocol-as-completed check: ok
```

### `python scripts/check_no_level2_as_level3.py`

```text
No-Level2-as-Level3 check: ok
```

### `python scripts/check_level3_gates.py`

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
```

### `python scripts/check_registry_to_tables.py`

```text
Registry-to-table consistency check: ok (3 main table records)
```

### `python scripts/check_main_results_from_registry.py`

```text
Main-results-from-registry check: ok
```

### `python scripts/check_artifact_registry_v2.py`

```text
Artifact registry v2 check: ok (143 records)
```

### `python scripts/check_filter_manifests.py --include-step4`

```text
Filter manifest check: ok (8 manifests)
```

### `python scripts/check_training_manifests.py --include-step5`

```text
Training manifest check: ok (1 manifests)
```

### `python scripts/check_urd_manifests.py --include-step6`

```text
URD manifest check: ok (3 manifests)
```

### `python scripts/check_evaluation_manifests.py --include-step7`

```text
Evaluation manifest check: ok (7 manifests)
```

### `python scripts/check_mechanism_manifests.py --include-step8`

```text
Mechanism manifest check: ok (9 manifests)
```

### `python scripts/write_step9_readiness_report.py`

```text
Step 9 readiness report: completed
Report: artifacts/reports/step9_readiness_report.json
```

