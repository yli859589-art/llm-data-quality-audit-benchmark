# Failure Cases

This page summarizes failure evidence from real artifacts, not hand-written
success claims.

## HDQS++ v1

HDQS++ v1 underperforms raw on the current WikiText-2 small-model matrix.
Diagnostic artifacts show that hard filtering can introduce distribution shift.

Source:

- `artifacts/diagnostics/hdqspp_failure_analysis.csv`
- `artifacts/stats/main_results.csv`

## HDQS++ v2

HDQS++ v2 improves token/length distribution diagnostics versus v1, but the
completed-training mean PPL is worse than raw and worse than v1.

Source:

- `artifacts/stats/method_comparison_summary.csv`
- `artifacts/methods/hdqspp_v2_design.json`

## HDQS++ v3

HDQS++ v3 removes token-frequency preservation, weakens length/distribution
constraints, and uses calibrated soft selection. It improves over v2 as a
secondary trend, but it still does not beat raw.

Source:

- `artifacts/methods/hdqspp_v3_design.json`
- `artifacts/stats/method_status_report.md`
- `artifacts/ablations/v3_model_ablation_results.csv`

## Length Filter

The length-only baseline is weak. It demonstrates that simple filtering can
remove useful distributional coverage.

Source:

- `artifacts/stats/main_results.csv`

## Random And Dedup

`random_same_keep_rate` and `dedup_only` remain close to raw. This is a useful
sanity check: complicated quality filters must beat simple baselines before
claiming value.

Source:

- `artifacts/stats/main_results.csv`

## Distribution Shift And Overfiltering Risk

Filtering can change token and length distributions even when the score seems
reasonable. The project treats this as an audit finding, not as a hidden
failure.
