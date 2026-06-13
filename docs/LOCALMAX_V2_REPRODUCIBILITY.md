# LocalMax V2 Reproducibility

Run order:

1. `python scripts/localmax_v2/check_localmax_v2_environment.py`
2. `python scripts/localmax_v2/audit_lm_metric_correctness.py`
3. `python scripts/localmax_v2/prepare_localmax_v2_data.py --config configs/localmax_v2/data_matrix.yaml`
4. `python scripts/localmax_v2/run_localmax_v2_filters.py --config configs/localmax_v2/filter_matrix.yaml`
5. `python scripts/localmax_v2/benchmark_training_throughput.py`
6. `python scripts/localmax_v2/run_localmax_v2_training.py --config configs/localmax_v2/training_matrix.yaml`
7. `python scripts/localmax_v2/run_localmax_v2_evaluation.py --config configs/localmax_v2/evaluation_matrix.yaml`
8. `python scripts/localmax_v2/run_localmax_v2_downstream.py --config configs/localmax_v2/downstream_matrix.yaml`
9. `python scripts/localmax_v2/run_localmax_v2_analysis.py --config configs/localmax_v2/mechanism_matrix.yaml`
10. `python scripts/localmax_v2/finalize_localmax_v2_execution.py`
11. `python scripts/localmax_v2/finalize_localmax_v2_release.py`

Text artifacts use UTF-8/LF canonical writing. PNG hashes are platform-dependent; source CSVs and generation scripts are the reproducibility anchors.
