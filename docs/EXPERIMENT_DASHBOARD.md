# Experiment Dashboard

- Readiness: `EXPERIMENT-CANDIDATE`
- Benchmark scope status: `multi_dataset_audit_candidate`
- Method status: `honest_audit_framework`
- Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`
- CCF-C ready: `false`
- Reporting contract: `docs/REPORTING_CONTRACT.md`

## Main Results Snapshot

| Method | Mean PPL | CI | Status |
|---|---:|---|---|
| `raw` | 12.6214 | [11.3111, 13.8532] | best current baseline |
| `random_same_keep_rate` | 12.7058 | [12.1098, 13.3843] | completed_training |
| `dedup_only` | 12.7261 | [12.1193, 13.6124] | completed_training |
| `length_filter` | 15.1600 | [13.6383, 17.6301] | completed_training |
| `hdqspp` | 13.2641 | [12.5662, 13.8293] | completed_training |
| `hdqspp_v2` | 14.1618 | [12.0612, 16.6940] | completed_training |
| `hdqspp_v3` | 13.2341 | [12.6644, 13.5224] | completed_training |

## Cross-Dataset Status

| Dataset | Status | Scope | Completed rows | Failed rows |
|---|---|---|---:|---:|
| `wikitext2_paper` | `real_local_nonfallback` | `official_split` | 12 | 0 |
| `openwebtext_streaming` | `real_nonfallback` | `streaming_sample` | 12 | 0 |
| `c4_en_streaming` | `real_nonfallback` | `streaming_sample` | 12 | 0 |

## Figures

- `artifacts/figures/project_pipeline.svg`
- `artifacts/figures/benchmark_protocol.svg`
- `artifacts/figures/method_comparison_ci.svg`
- `artifacts/figures/main_results_leaderboard.svg`
- `artifacts/figures/failure_mode_summary.svg`
- `artifacts/figures/artifact_lineage_overview.svg`
- `artifacts/figures/cross_dataset_method_comparison.svg`
- `artifacts/figures/dataset_status_matrix.svg`

## Interpretation

The current WikiText-2 small-model evidence shows raw as the strongest mean PPL baseline. HDQS++ v3 improves over v2 as a secondary trend, but it does not support a method claim over raw.

3B adds OpenWebText and C4 English real streaming samples. They are bounded samples, and cross-dataset tables preserve completed, lightweight, failed, and configured states.

The project value is the audit trail: real data, fair baselines, append-only registry, artifact lineage, failure cases, and reproducible release checks.
