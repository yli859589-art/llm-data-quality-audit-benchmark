# Reproducibility

Reproducibility claims in this file follow `docs/REPORTING_CONTRACT.md`. The
commands reproduce an audit benchmark and should not be described as proving
HDQS++ v3 improvement over raw.

## Python Version

Use Python 3.10 or newer. The current local release checks were run with the
Python interpreter available in this workspace.

## Dependencies

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## Data Preparation

WikiText-2 real local data is prepared with fallback disabled:

```bash
python scripts/prepare_real_data.py --config configs/data/wikitext2_paper.yaml
python scripts/check_split_integrity.py
python scripts/check_no_fallback_in_experiments.py
```

3B streaming samples are prepared with fallback disabled:

```bash
python scripts/prepare_streaming_data.py --config configs/data/openwebtext_streaming.yaml
python scripts/prepare_streaming_data.py --config configs/data/c4_en_streaming.yaml
```

The generated manifests and dataset cards state `dataset_scope=streaming_sample`
and `is_full_dataset=false`.

## Run Registry

All training and filtering actions are recorded in:

- `artifacts/runs/run_registry.jsonl`
- `artifacts/runs/run_registry.csv`

The registry is append-oriented. Do not delete failed or superseded rows to make
the project look cleaner.

## Artifact Hashes

Artifact lineage is checked with:

```bash
python scripts/check_artifact_lineage.py
```

Superseded same-path artifacts are allowed only when newer registry rows explain
the replacement.

## Environment Fingerprint

```bash
python scripts/capture_environment.py
```

Output:

- `artifacts/environment/fingerprint.json`

## Rebuild Main Results

```bash
python scripts/analyze_significance.py --input artifacts/runs/run_registry.csv --output artifacts/stats
python scripts/generate_tables.py
python scripts/check_main_results_purity.py
```

## Rebuild Cross-Dataset Audit

```bash
python scripts/generate_cross_dataset_tables.py
python scripts/analyze_cross_dataset_audit.py
```

Cross-dataset outputs are separate from `main_results.csv`.

## Verify Split Integrity

```bash
python scripts/check_split_integrity.py
```

## Verify No Test Leakage

```bash
python scripts/check_no_test_leakage.py
```

## Clean Cache Without Removing Evidence

```bash
python scripts/clean_project_artifacts.py
```

This only removes generated cache/temp paths. It preserves registry, stats,
diagnostics, main results, and audit artifacts.

On Windows, use `mingw32-make check` and `mingw32-make release-check` when the
plain `make` command is not installed.
