# Final Release Report

- Status: `release_candidate`
- Version: `3C-3-release-candidate-v1`
- readiness: `EXPERIMENT-CANDIDATE`
- method_status: `honest_audit_framework`
- benchmark_scope_status: `multi_dataset_audit_candidate`
- secondary_method_finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`
- ccf_c_ready: `false`
- main_results_modified: `false`
- experiment_results_modified: `false`

## Fresh-Unzip Status

- fresh-unzip status: `passed`
- fresh-unzip lightweight_check_status: `passed`
- fresh-unzip heavy_check_status: `skipped_by_request`
- fresh-unzip heavy_check_reason: skip-heavy flag was provided

A skipped heavy check is reported as `skipped_by_request`, not as passed.

## Validation Commands

| Command group | Status |
|---|---|
| `check_experiment_readiness` | `passed` |
| `check_repo_clean` | `passed` |
| `claim_hygiene` | `passed` |
| `make_check` | `not_run_due_to_environment` |
| `make_release_check` | `not_run_due_to_environment` |
| `mingw32_make_check` | `passed` |
| `mingw32_make_release_check` | `passed` |
| `pytest_69` | `passed` |
| `run_all_checks_timeout_300` | `passed` |
| `run_release_checks_timeout_300` | `passed` |
| `verify_fresh_unzip_skip_heavy` | `passed` |

## Zip Cleanliness

- zip status: `passed`
- zip file name: `llm_data_quality_audit_benchmark_release_candidate_v1.zip`
- zip path: `<local_user_path>`
- zip SHA-256: `70c3c1746485e3b3245984f5faa2a6c62ec3087a97f0630d129a7f9d4dc2f5d8`
- zip size bytes: `7294608`
- zip entry count: `833`
- missing required entries: `0`
- cache hits: `0`
- nested zip hits: `0`
- local absolute path hits: `0`

## Protected Result Hashes

| File | Matches expected | Actual SHA-256 |
|---|---|---|
| `artifacts/tables/main_results.csv` | `True` | `eab3478d19e04caf97e07fc31fcd3cc36089c19320a64e96f7bac9eb12d89921` |
| `artifacts/cross_dataset/cross_dataset_results.csv` | `True` | `8da3e015146193fcd5d1f5f47a9e0a5ed84f55a4182b4bb5932dc657b8daad4c` |
| `artifacts/runs/run_registry.jsonl` | `True` | `a05a06fca305cedf2c46dbead17ac222a5f09e73ab105538479a049df90a26ce` |
| `artifacts/stats/main_results.csv` | `True` | `e40944bb6476d84e8c3fc65670b2dc5e7db62cf47ca7fc6d0051768458cd0e32` |
| `artifacts/experiment_readiness_report.json` | `True` | `9456f46adc79f21026439a5b6504f14c3029022afe977f3ca066d6c2c513f1e1` |

## Release Boundary

- Audit benchmark release candidate.
- HDQS++ v3 does not outperform raw under the current fair benchmark.
- OpenWebText/C4 evidence is streaming-sample evidence only.
- No new 4A experiments are included in this release.

## 4A Roadmap Not Executed

- BPE tokenizer
- medium model
- larger OpenWebText/C4 streaming samples
- stronger seed budget
- held-out test evaluation after freezing
- compute logs and larger-scale mechanism diagnostics
