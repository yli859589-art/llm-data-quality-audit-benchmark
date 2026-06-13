# Run All Checks Report

- Status: `passed`
- Overall passed: `True`
- Started at: `2026-06-13T11:42:03+00:00`
- Finished at: `2026-06-13T11:42:04+00:00`
- Duration seconds: `1.107`
- Failed groups: `none`
- Timeout groups: `none`
- Skipped groups: `legacy_core_tests, step2_data_tests, step3_tokenizer_tests, step4_filter_tests, step5_training_tests, step6_urd_tests, step7_evaluation_tests, step8_mechanism_tests, step9_readiness_tests, step10A_protocol_tests, step10B_execution_tests, step10B_localmax_tests, step10C_localmax_release_tests, localmax_v2_tests, manifest_checks, artifact_checks, claim_checks, level3_gate_checks, level3_execution_checks, localmax_execution_checks, localmax_release_checks, localmax_v2_execution_checks, localmax_v2_release_checks, registry_finalization_checks`

| Group | Required | Status | Return Code | Duration Seconds |
|---|---:|---|---:|---:|
| `localmax_ccfc_tests` | `True` | `passed` | 0 | 0.865 |
| `localmax_ccfc_artifact_checks` | `True` | `passed` | 0 | 0.242 |

## Command Tails

### localmax_ccfc_tests

- Command: `python -m pytest tests/test_localmax_ccfc_strengthening.py -q`
- Status: `passed`

```text
....                                                                     [100%]
4 passed in 0.09s
```

### localmax_ccfc_artifact_checks

- Command: `python scripts/localmax_ccfc/check_ccfc_artifacts.py ; python scripts/localmax_ccfc/finalize_ccfc_project.py`
- Status: `passed`

```text
{"blocking_failures": [], "ccfc_artifact_check_passed": true, "expected_training_runs": 42}
{"ccfc_candidate_ready": true, "current_readiness": "TOP_TIER_CCFC_PROJECT_CANDIDATE"}
```

