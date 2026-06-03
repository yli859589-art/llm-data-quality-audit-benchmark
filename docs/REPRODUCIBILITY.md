# Reproducibility

## Environment

- Python `3.10+`
- Runtime dependencies: NumPy and PyTorch
- Default device: CPU
- CI thread limits: `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`
- Quick seed: `23`
- Paper-prototype seeds: `23`, `42`, `3407`

## Recommended Setup

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -e .
python -m unittest discover -s tests -v
```

The editable install is the recommended path because it matches CI and makes
`course_project_suite` importable without manually setting `PYTHONPATH`.

Fallback without installation:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Acceptance Commands

```bash
python scripts/check_repo.py --clean
python -m unittest discover -s tests -v
python scripts/run_quick_experiment.py
python scripts/tune_hdqs_quick.py
python scripts/run_dataset_matrix.py --mode quick
python scripts/run_dataset_matrix.py --mode paper-prototype --dry-run
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/statistical_analysis.py
python scripts/make_research_tables.py
python scripts/make_research_figures.py
python scripts/analyze_failures.py
python scripts/make_project_report.py
python scripts/check_artifacts.py
python all_course_projects.py --self-check --json
python scripts/run_coverage.py
ruff check .
black --check .
mypy src/course_project_suite/llm_benchmark
```

`black --check .` depends on a supported local Python interpreter. If Black
refuses to run because of an interpreter safety guard, record that in the final
verification report instead of claiming a pass.

## Artifact Policy

Tables and figures are generated from JSON/CSV artifacts; do not hand-edit
result claims. Final ZIP packaging excludes `.git`, Python caches, tool caches,
temporary benchmark outputs, and machine-specific absolute paths.
