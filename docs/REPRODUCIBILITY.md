# Reproducibility

## Environment

- Python `3.10+`
- Runtime dependencies: NumPy and PyTorch
- Default device: CPU
- CI thread limits: `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`
- Default quick seed: `23`
- Full seeds: `23`, `42`, `3407`

## Offline Acceptance Commands

```bash
python scripts/check_repo.py
python scripts/run_quick_experiment.py
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/check_artifacts.py
python -m pytest tests -q
ruff check .
black --check .
mypy src
```

Run `python scripts/run_coverage.py` when `coverage` is installed. Generated
quick artifacts live under `artifacts/quick_experiment/`.

## Artifact Policy

Tables and figures are generated from `results.json`; do not hand-edit result
claims. Final ZIP packaging excludes `.git`, Python caches, tool caches,
temporary benchmark outputs, and machine-specific absolute paths.
