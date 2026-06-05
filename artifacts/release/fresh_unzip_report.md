# Fresh-Unzip Verification Report

- Status: `passed`
- Zip file name: `llm_data_quality_audit_benchmark_release_candidate_v1.zip`
- Zip path: `<local_user_path>`
- Zip SHA-256: `70c3c1746485e3b3245984f5faa2a6c62ec3087a97f0630d129a7f9d4dc2f5d8`
- lightweight_check_status: `passed`
- heavy_check_status: `skipped_by_request`
- heavy_check_reason: skip-heavy flag was provided

## Structure Checks

- Missing required files: `0`
- Cache files in zip: `0`
- Nested zip files: `0`
- Local absolute path hits: `0`
- cache_scan_status: `passed`
- nested_zip_scan_status: `passed`
- local_absolute_path_scan_status: `passed`

## Checked Files

- `README.md`
- `Makefile`
- `PROJECT_SUMMARY.md`
- `PROJECT_ONE_PAGE.md`
- `TECHNICAL_OVERVIEW.md`
- `DEMO_GUIDE.md`
- `RESUME_BULLETS.md`
- `scripts/run_all_checks.py`
- `scripts/run_release_checks.py`
- `scripts/check_experiment_readiness.py`
- `scripts/check_claim_hygiene.py`
- `scripts/verify_fresh_unzip.py`
- `scripts/generate_final_release_report.py`
- `artifacts/tables/main_results.csv`
- `artifacts/release/fresh_unzip_report.json`
- `artifacts/release/fresh_unzip_report.md`
- `artifacts/release/final_release_report.json`
- `artifacts/release/final_release_report.md`
- `docs/QUICKSTART.md`
- `docs/README.md`
- `docs/REPORTING_CONTRACT.md`
- `docs/FIGURE_INDEX.md`
- `docs/PROJECT_PRESENTATION_NOTES.md`
- `docs/future_publication_notes/README.md`

## Lightweight Steps

| Step | Status | Return code |
|---|---|---:|
| `check_experiment_readiness` | `passed` | 0 |
| `check_claim_hygiene` | `passed` | 0 |
| `run_release_checks_skip_core_zip` | `passed` | 0 |

## Heavy Steps

| Step | Status | Return code |
|---|---|---:|
| `run_all_checks` | `skipped_by_request` |  |
