# Cross-Dataset Audit

This report expands the project from a single WikiText-2 audit candidate toward a multi-dataset audit benchmark.
It follows `docs/REPORTING_CONTRACT.md` and does not claim supported improvement over raw across datasets.

## Dataset Status

| Dataset | Status | Scope | Completed rows | Failed rows | Failure reason |
|---|---|---|---:|---:|---|
| wikitext2_paper | `real_local_nonfallback` | `official_split` | 12 | 0 |  |
| openwebtext_streaming | `real_nonfallback` | `streaming_sample` | 12 | 0 |  |
| c4_en_streaming | `real_nonfallback` | `streaming_sample` | 12 | 0 |  |

## Audit Findings

- Raw baseline status: raw has completed rows on 3 dataset(s).
- Raw/random/dedup stability: raw and dedup_only are the closest baselines in the completed rows; random_same_keep_rate is more variable on streaming samples.
- HDQS++ v3 status: HDQS++ v3 does not outperform raw by mean PPL on the completed datasets: c4_en_streaming: hdqspp_v3 mean PPL 302.9781 is above raw (raw 174.5871); openwebtext_streaming: hdqspp_v3 mean PPL 253.3836 is above raw (raw 133.5411); wikitext2_paper: hdqspp_v3 mean PPL 13.2341 is above raw (raw 12.6214).
- Perplexity comparisons across datasets are not direct method claims unless tokenizer hash, vocabulary size, parameter count, and token budget match.
- Failed OpenWebText/C4 states, if present, are retained as audit evidence rather than hidden.

## Generated Figures

- `artifacts/figures/cross_dataset_method_comparison.svg`
- `artifacts/figures/cross_dataset_keep_rate.svg`
- `artifacts/figures/cross_dataset_distribution_shift.svg`
- `artifacts/figures/dataset_status_matrix.svg`
- `artifacts/figures/filter_failure_modes_by_dataset.svg`
