# Release Checklist

This checklist follows `docs/REPORTING_CONTRACT.md`. The release is an audit
benchmark and does not claim that HDQS++ v3 outperforms raw under the current
fair benchmark.

## Core Checks

- [ ] `python scripts/check_repo.py --clean`
- [ ] `python -m pytest -q`
- [ ] `python scripts/check_claim_hygiene.py`
- [ ] `python scripts/run_all_checks.py --timeout 300`
- [ ] `python scripts/run_release_checks.py --timeout 300`
- [ ] `python scripts/verify_fresh_unzip.py --zip <release-zip> --timeout 300 --skip-heavy`
- [ ] `python scripts/check_experiment_readiness.py`

## Fresh-Unzip Checks

- [ ] Build release zip without cache files or nested old zips.
- [ ] Include `artifacts/release/fresh_unzip_report.json`.
- [ ] Include `artifacts/release/fresh_unzip_report.md`.
- [ ] Include `artifacts/release/final_release_report.json`.
- [ ] Include `artifacts/release/final_release_report.md`.
- [ ] `python scripts/verify_fresh_unzip.py --zip <release-zip> --timeout 300 --skip-heavy`
- [ ] `python scripts/run_release_checks.py --skip-core-checks --zip <release-zip>`
- [ ] Report `heavy_check_status` as `skipped_by_request` when `--skip-heavy`
      is used; do not mark skipped heavy checks as passed.

## Make Entry Points

- [ ] On Unix-like systems with GNU Make: `make check`
- [ ] On Unix-like systems with GNU Make: `make release-check`
- [ ] On Windows with MinGW Make: `mingw32-make check`
- [ ] On Windows with MinGW Make: `mingw32-make release-check`
- [ ] If make is not installed, record `not run due to environment`.

## Release Package Cleanliness

- [ ] No `__pycache__`
- [ ] No `.pyc`
- [ ] No `.pytest_cache`
- [ ] No `.ruff_cache`
- [ ] No `.mypy_cache`
- [ ] No notebook checkpoints
- [ ] No nested old zip files
- [ ] No local absolute paths in runnable commands, configs, manifests, or release claims
- [ ] Includes `README.md`
- [ ] Includes `PROJECT_ONE_PAGE.md`
- [ ] Includes `PROJECT_SUMMARY.md`
- [ ] Includes `TECHNICAL_OVERVIEW.md`
- [ ] Includes `DEMO_GUIDE.md`
- [ ] Includes `RESUME_BULLETS.md`
- [ ] Includes `docs/README.md`
- [ ] Includes `docs/REPORTING_CONTRACT.md`
- [ ] Includes `docs/PROJECT_PRESENTATION_NOTES.md`
- [ ] Includes `docs/FIGURE_INDEX.md`
- [ ] Includes `docs/future_publication_notes/README.md`
- [ ] Includes `scripts/check_claim_hygiene.py`
- [ ] Includes `scripts/verify_fresh_unzip.py`
- [ ] Includes `scripts/generate_final_release_report.py`
- [ ] Includes `artifacts/tables/main_results.csv`
- [ ] Includes `artifacts/cross_dataset/` if 3B cross-dataset evidence is present
- [ ] Includes `artifacts/release/final_release_report.json`
- [ ] Includes `artifacts/release/final_release_report.md`

## Status Confirmation

- [ ] readiness remains `EXPERIMENT-CANDIDATE`
- [ ] method_status remains `honest_audit_framework`
- [ ] ccf_c_ready remains `false`
- [ ] `main_results.csv` was not manually edited
- [ ] `run_registry.jsonl` history was not deleted
- [ ] paper/reviewer/submission notes are archived under `docs/future_publication_notes/`
