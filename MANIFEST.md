# Manifest

This manifest describes the release-candidate package for the LLM Data Quality
Diagnostics and Risk Auditing Benchmark.

## Included Directories

- `configs/`: data, experiment, model, filter, and frozen configuration files.
- `data/`: small sample data and local real WikiText-2 split files.
- `src/`: reusable data, diagnostics, filtering, model, and benchmark code.
- `scripts/`: runners, checks, release tooling, and table/figure/dashboard generators.
- `tests/`: automated tests.
- `artifacts/`: generated evidence files, release reports, tables, and figures.
- `docs/`: GitHub-facing documentation and audit reports.
- `docs/future_publication_notes/`: archived paper/reviewer/submission notes.
- `.github/`: CI workflow.

## Core Entry Points

- `README.md`
- `PROJECT_ONE_PAGE.md`
- `PROJECT_SUMMARY.md`
- `TECHNICAL_OVERVIEW.md`
- `DEMO_GUIDE.md`
- `RESUME_BULLETS.md`
- `docs/README.md`
- `docs/QUICKSTART.md`
- `docs/BENCHMARK_PROTOCOL.md`
- `docs/REPRODUCIBILITY.md`
- `docs/REPORTING_CONTRACT.md`
- `docs/PROJECT_STATUS.md`
- `docs/CROSS_DATASET_AUDIT.md`
- `docs/PROJECT_PRESENTATION_NOTES.md`
- `docs/FIGURE_INDEX.md`
- `docs/ARTIFACT_INDEX.md`

## Core Artifacts

- `artifacts/runs/run_registry.jsonl`
- `artifacts/runs/run_registry.csv`
- `artifacts/tables/main_results.csv`
- `artifacts/stats/main_results.csv`
- `artifacts/stats/method_status_report.md`
- `artifacts/cross_dataset/cross_dataset_results.csv`
- `artifacts/cross_dataset/dataset_status_matrix.csv`
- `artifacts/release/claim_hygiene_report.json`
- `artifacts/release/fresh_unzip_report.json`
- `artifacts/release/final_release_report.json`

## Legacy And Superseded Artifacts

Legacy and superseded artifacts are retained for audit lineage. Failed or
superseded runs must not be deleted to make the project look cleaner. The
lineage checker reports superseded same-path hashes instead of silently hiding
old evidence.

Publication drafts, reviewer notes, and submission readiness notes are archived
under `docs/future_publication_notes/`. They are future research notes, not
current release claims.

## Run Checks

```bash
python scripts/check_repo.py --clean
python -m pytest -q
python scripts/check_claim_hygiene.py
python scripts/run_all_checks.py --timeout 300
python scripts/run_release_checks.py --timeout 300
python scripts/verify_fresh_unzip.py --zip path/to/release.zip --timeout 300 --skip-heavy
python scripts/check_experiment_readiness.py
```

## Verify A Clean Zip

The release zip should not contain `__pycache__`, `.pyc`, `.pytest_cache`,
`.ruff_cache`, `.mypy_cache`, notebook checkpoints, nested old zip files, or
local absolute paths. Validate with:

```bash
python scripts/verify_fresh_unzip.py --zip path/to/release.zip --timeout 300 --skip-heavy
python scripts/run_release_checks.py --skip-core-checks --zip path/to/release.zip
```

## Claim Boundary

The release is an audit benchmark. It does not claim that HDQS++ v3 outperforms
raw under the current fair benchmark, and it is not a CCF-C-ready paper artifact.
