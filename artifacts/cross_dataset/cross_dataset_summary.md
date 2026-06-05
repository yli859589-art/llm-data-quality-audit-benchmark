# Cross-Dataset Audit Summary

This artifact separates completed, lightweight, failed, and configured-only rows.
Streaming samples are bounded samples, not complete upstream corpora.

## Dataset Status

| Dataset | Status | Scope | Completed rows | Failed rows | Failure reason |
|---|---|---|---:|---:|---|
| wikitext2_paper | `real_local_nonfallback` | `official_split` | 12 | 0 |  |
| openwebtext_streaming | `real_nonfallback` | `streaming_sample` | 12 | 0 |  |
| c4_en_streaming | `real_nonfallback` | `streaming_sample` | 12 | 0 |  |

## Completed Training Means

- `c4_en_streaming` / `dedup_only` mean PPL: `174.5871`
- `c4_en_streaming` / `hdqspp_v3` mean PPL: `302.9781`
- `c4_en_streaming` / `random_same_keep_rate` mean PPL: `182.1845`
- `c4_en_streaming` / `raw` mean PPL: `174.5871`
- `openwebtext_streaming` / `dedup_only` mean PPL: `133.5411`
- `openwebtext_streaming` / `hdqspp_v3` mean PPL: `253.3836`
- `openwebtext_streaming` / `random_same_keep_rate` mean PPL: `220.1726`
- `openwebtext_streaming` / `raw` mean PPL: `133.5411`
- `wikitext2_paper` / `dedup_only` mean PPL: `12.7261`
- `wikitext2_paper` / `hdqspp_v3` mean PPL: `13.2341`
- `wikitext2_paper` / `random_same_keep_rate` mean PPL: `12.7058`
- `wikitext2_paper` / `raw` mean PPL: `12.6214`

## Interpretation Boundary

- Do not compare perplexity across datasets unless tokenizer hash, vocabulary size, parameter count, and token budget match.
- Failed datasets remain visible in `dataset_status_matrix.csv` and `cross_dataset_failures.csv`.
- This is an audit benchmark expansion, not a supported over-raw method claim.
