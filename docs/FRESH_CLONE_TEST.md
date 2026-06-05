# Fresh Clone / Clean Copy Test

Use this guide to validate the release from a fresh clone or clean copy. If no
remote repository is available, unzip the release package into a clean directory
and run the same commands there.

The current release is an audit benchmark. These commands do not prove that
HDQS++ v3 outperforms raw; they validate reproducibility, claim hygiene, and
release structure.

## Linux / macOS

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/run_all_checks.py --timeout 300
python scripts/run_release_checks.py --timeout 300
python scripts/check_experiment_readiness.py
```

If GNU Make is available:

```bash
make check
make release-check
```

If `make` is not available, report the make target as `not run due to environment`.

## Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts/run_all_checks.py --timeout 300
python scripts/run_release_checks.py --timeout 300
python scripts/check_experiment_readiness.py
```

If Windows has TDM-GCC / MinGW Make:

```powershell
mingw32-make check
mingw32-make release-check
```

If neither `make` nor `mingw32-make` exists, report those checks as
`not run due to environment`; do not mark them as passed.

## Zip Fresh-Unzip Verification

```bash
python scripts/verify_fresh_unzip.py --zip path/to/release.zip --timeout 300 --skip-heavy
```

The script writes:

- `artifacts/release/fresh_unzip_report.json`
- `artifacts/release/fresh_unzip_report.md`

When `--skip-heavy` is used, the report must show
`heavy_check_status=skipped_by_request`; a skipped heavy check must not be
reported as passed.

The final release candidate also includes:

- `artifacts/release/final_release_report.json`
- `artifacts/release/final_release_report.md`
