# Reporting Contract

This document is the canonical public-reporting contract for the project. README,
dashboards, evidence maps, summaries, and release notes must follow this wording
when describing project status and claims.

## 1. Project Positioning

Canonical project name:

`LLM Data Quality Diagnostics and Risk Auditing Benchmark`

This project provides a reproducible benchmark for auditing the risks of LLM
data-quality filtering methods. It is not a method-success paper claiming that
HDQS++ has been shown to outperform raw training data.

## 2. Current Release Status

- readiness = `EXPERIMENT-CANDIDATE`
- method_status = `honest_audit_framework`
- ccf_c_ready = `false`
- benchmark_scope_status = `multi_dataset_audit_candidate`

The status means the repository is a credible experiment-candidate audit
benchmark with real data, fair baselines, artifact lineage, and claim-safety
checks. It is not a final CCF-C-ready paper artifact.

## 3. Canonical Claim Boundary

Allowed claims:

- This project provides a reproducible audit benchmark for LLM data quality filtering.
- HDQS++ v3 improves over HDQS++ v2 trend-wise but does not outperform raw under the current fair benchmark.
- Raw, `random_same_keep_rate`, and `dedup_only` remain strong baselines in the current setting.
- The project shows that heuristic data quality filtering can harm validation perplexity under fair tokenizer/model/evaluation settings.
- OpenWebText/C4 results, if present, are real streaming-sample audits, not full-dataset results.

Forbidden claims:

- HDQS++ beats raw.
- HDQS++ outperforms raw.
- HDQS++ improves LLM pretraining.
- HDQS++ is state-of-the-art.
- CCF-C ready.
- Full OpenWebText benchmark.
- Full C4 benchmark.
- Large-scale web corpus result, unless truly large-scale.
- Statistically significant improvement over raw, unless supported by valid seed count and CI.

## 4. Canonical Results

Lower mean PPL is better. These rows are current canonical release evidence and
must be interpreted within each dataset scope.

| Dataset | dataset_scope | Method | Mean PPL | Safe interpretation |
|---|---|---|---:|---|
| `wikitext2_paper` | `official_split` | `raw` | 12.6214 | Strongest current WikiText-2 mean baseline. |
| `wikitext2_paper` | `official_split` | `random_same_keep_rate` | 12.7058 | Close baseline; no supported method win over raw. |
| `wikitext2_paper` | `official_split` | `dedup_only` | 12.7261 | Close baseline; exact dedup is competitive. |
| `wikitext2_paper` | `official_split` | `hdqspp_v3` | 13.2341 | Improves over v2 trend-wise, but does not outperform raw. |
| `openwebtext_streaming` | `streaming_sample` | `raw` | 133.5411 | Strongest current OpenWebText streaming-sample mean baseline. |
| `openwebtext_streaming` | `streaming_sample` | `random_same_keep_rate` | 220.1726 | More variable than raw on this streaming sample. |
| `openwebtext_streaming` | `streaming_sample` | `dedup_only` | 133.5411 | Matches raw in the current streaming-sample run. |
| `openwebtext_streaming` | `streaming_sample` | `hdqspp_v3` | 253.3836 | Does not outperform raw on this streaming sample. |
| `c4_en_streaming` | `streaming_sample` | `raw` | 174.5871 | Tied with dedup as the strongest current C4 streaming-sample mean baseline. |
| `c4_en_streaming` | `streaming_sample` | `random_same_keep_rate` | 182.1845 | Close but more variable than raw/dedup. |
| `c4_en_streaming` | `streaming_sample` | `dedup_only` | 174.5871 | Tied with raw in the current streaming-sample run. |
| `c4_en_streaming` | `streaming_sample` | `hdqspp_v3` | 302.9781 | Does not outperform raw on this streaming sample. |

Canonical result interpretation: raw is currently the strongest or tied-strongest
baseline in the completed settings. HDQS++ v3 has not outperformed raw under the
fair benchmark.

## 5. Dataset Scope Rules

- `official_split`: official or locally materialized official split used for the main candidate matrix.
- `streaming_sample`: bounded streaming sample from a real upstream dataset.
- `local_real_subset`: local real-data subset that is not the full upstream corpus.
- `full_dataset`: complete upstream dataset run; this label must not be used unless the complete upstream dataset was actually processed.

A `streaming_sample` must not be described as a `full_dataset`, web-scale result,
or complete OpenWebText/C4 benchmark.

## 6. Method Status Rules

Canonical primary status:

`method_status = honest_audit_framework`

Allowed secondary method finding:

HDQS++ v3 improves over v2 trend-wise but not over raw.

Do not rewrite this status as `method_supported_over_raw`, `supported_over_raw`,
or any positive method-success claim.

## 7. Known Limitations

- The current model scale is `small`.
- The current tokenizer/model setting is limited and should not be generalized as a broad LLM pretraining result.
- OpenWebText/C4 evidence is based on real streaming samples, not complete upstream corpora.
- The release does not make a CCF-C-ready claim.
- Method improvement over raw is unsupported in the current evidence.
- Held-out test evaluation should only be used after method settings are frozen.
- Failed and superseded runs remain part of the audit trail and must not be deleted to beautify results.
