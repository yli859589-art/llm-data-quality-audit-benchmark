# LocalMax Reproducibility

Current status: `LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED`

Level 3 status: `not completed`

## Environment

The environment report is stored at `artifacts/reports/localmax_environment_report.json`.

## Pipeline Commands

```bash
python scripts/localmax/prepare_localmax_tokenizer.py --config configs/localmax/tokenizer.yaml
python scripts/localmax/prepare_localmax_data_minimal.py --config configs/localmax/data_matrix_minimal.yaml
python scripts/localmax/run_localmax_filters_minimal.py --config configs/localmax/filter_matrix_minimal.yaml
python scripts/localmax/run_localmax_training_strengthened.py --config configs/localmax/training_strengthened.yaml
python scripts/localmax/run_localmax_evaluation_strengthened.py
python scripts/localmax/run_localmax_analysis_strengthened.py
python scripts/localmax/finalize_localmax_release.py
```

## Hash Checks

The release manifest records table, figure, document, and report hashes. Historical main results have protected hashes and are checked by `scripts/check_main_results_purity.py`.

## Checkpoint Policy

Full binary checkpoints are not stored in the repository; training manifests, metrics, lineage, and state fingerprints are preserved.

## Bundle Scope

Bundle scope: `standalone_metadata_bundle`.

The LocalMax release bundle is self-contained for metadata review. Raw data and binary checkpoints are intentionally excluded. Release-table manifest links point inside `artifacts/localmax_release/manifests/`.

## Canonical Text Policy

Generated text artifacts use UTF-8, LF newlines, stable JSON key ordering, stable JSON indentation, and a final newline at EOF. Registry finalization runs after all release-writing commands.
