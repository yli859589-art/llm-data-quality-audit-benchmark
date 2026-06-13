# Run All Checks Report

- Status: `passed`
- Overall passed: `True`
- Started at: `2026-06-11T11:59:48+00:00`
- Finished at: `2026-06-11T11:59:50+00:00`
- Duration seconds: `2.301`
- Failed groups: `none`
- Timeout groups: `none`
- Skipped groups: `legacy_core_tests, step2_data_tests, step3_tokenizer_tests, step4_filter_tests, step5_training_tests, step6_urd_tests, step7_evaluation_tests, step8_mechanism_tests, manifest_checks, artifact_checks, claim_checks, level3_gate_checks`

| Group | Required | Status | Return Code | Duration Seconds |
|---|---:|---|---:|---:|
| `step9_readiness_tests` | `True` | `passed` | 0 | 2.301 |

## Command Tails

### step9_readiness_tests

- Command: `python -m pytest tests/test_step9_level3_artifact_hygiene.py -q`
- Status: `passed`

```text
........                                                                 [100%]
8 passed in 1.47s
```

