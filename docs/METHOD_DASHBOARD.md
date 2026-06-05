# Method Dashboard

- Readiness: `EXPERIMENT-CANDIDATE`
- Benchmark scope status: `multi_dataset_audit_candidate`
- Method status: `honest_audit_framework`
- Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`
- ccf_c_ready: `false`
- Repositioned as audit/diagnostics framework: `true`

## Main Results

| Method | Seeds | Mean PPL | CI | Train tokens | Eval validation tokens |
|---|---:|---:|---|---:|---:|
| `raw` | 3 | 12.6214 | [11.3111, 13.8532] | 1228800 | 53248 |
| `random_same_keep_rate` | 3 | 12.7058 | [12.1098, 13.3843] | 1228800 | 53248 |
| `dedup_only` | 3 | 12.7261 | [12.1193, 13.6124] | 1228800 | 53248 |
| `hdqspp` | 3 | 13.2641 | [12.5662, 13.8293] | 1228800 | 53248 |
| `hdqspp_v2` | 3 | 14.1618 | [12.0612, 16.6940] | 1228800 | 53248 |
| `hdqspp_v2_no_token_frequency` | 3 | 14.2653 | [12.0899, 15.9603] | 1228800 | 53248 |
| `hdqspp_v3` | 3 | 13.2341 | [12.6644, 13.5224] | 1228800 | 53248 |

## Figures

- `artifacts/figures/method_comparison_ci.svg`
- `artifacts/figures/v3_vs_baselines.svg`
- `artifacts/figures/keep_rate_vs_ppl.svg`
- `artifacts/figures/distribution_shift_vs_ppl.svg`
- `artifacts/figures/component_effects_v3.svg`
- `artifacts/figures/promising_variant_selection.svg`

## Interpretation

The project demonstrates a reproducible data-quality risk audit loop: real data, fair baselines, frozen configs, registry lineage, diagnostics, ablations, and claim-safety reporting.

The method claim remains limited by 3 seeds, small model scale, streaming-sample scope for OpenWebText/C4, and the fact that filtering does not outperform raw.
