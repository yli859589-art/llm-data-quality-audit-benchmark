# Quickstart

This quickstart uses existing WikiText-2 completed-training artifacts by
default. It does not rerun expensive training unless `--train` is passed.

## 1. Environment

Use Python 3.10+.

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

## 2. Minimal Benchmark

Validate the minimal raw/dedup/HDQS++ v3 loop without writing new
`main_results` rows:

```bash
python scripts/run_minimal_benchmark.py --quick-check
```

To train missing minimal rows explicitly:

```bash
python scripts/run_minimal_benchmark.py --train --methods raw dedup_only hdqspp_v3 --seeds 1
```

## 3. Run Checks

```bash
python scripts/run_all_checks.py
```

On Windows, if `make` is unavailable but MinGW Make is installed, use:

```bash
mingw32-make check
mingw32-make release-check
```

## 4. Generate Main Tables

```bash
python scripts/analyze_significance.py --input artifacts/runs/run_registry.csv --output artifacts/stats
python scripts/generate_tables.py
python scripts/check_main_results_purity.py
```

## 5. View Dashboards

```bash
python scripts/generate_figures.py
python scripts/generate_project_dashboard.py
```

Read:

- `docs/EXPERIMENT_DASHBOARD.md`
- `docs/METHOD_DASHBOARD.md`
- `docs/PROJECT_EVIDENCE_MAP.md`

## 5B. Cross-Dataset Streaming Audit

Prepare bounded real streaming samples:

```bash
python scripts/prepare_streaming_data.py --config configs/data/openwebtext_streaming.yaml
python scripts/prepare_streaming_data.py --config configs/data/c4_en_streaming.yaml
```

Run the 3B audit methods:

```bash
python scripts/run_audit_benchmark.py --config configs/experiments/openwebtext_dev.yaml --methods raw random_same_keep_rate dedup_only HDQS++v3 --seeds 1 2 3
python scripts/run_audit_benchmark.py --config configs/experiments/c4_en_dev.yaml --methods raw random_same_keep_rate dedup_only HDQS++v3 --seeds 1 2 3
python scripts/generate_cross_dataset_tables.py
python scripts/analyze_cross_dataset_audit.py
```

Read `docs/CROSS_DATASET_AUDIT.md`. These rows are separate from
`artifacts/tables/main_results.csv`.

## 6. Common Failure Causes

- Missing dependencies: rerun the install commands.
- Cache artifacts left in the tree: run `python scripts/clean_project_artifacts.py`.
- Missing registry rows: use `python scripts/run_minimal_benchmark.py --train`.
- Method status mismatch: rerun `python scripts/analyze_significance.py --input artifacts/runs/run_registry.csv --output artifacts/stats`.

## 7. Confirm No Fallback

```bash
python scripts/check_no_fallback_in_experiments.py
python scripts/check_split_integrity.py
```

The real data manifest is `artifacts/data/wikitext2_paper/data_manifest.json`.

## 8. Confirm `main_results` Is Rebuildable

```bash
python scripts/generate_tables.py
python scripts/check_main_results_purity.py
python scripts/check_artifact_lineage.py
```
