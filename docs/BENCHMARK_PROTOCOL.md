# Benchmark Protocol

This protocol follows `docs/REPORTING_CONTRACT.md`: the release is an audit
benchmark, not a claim that HDQS++ v3 outperforms raw.

## Dataset State

The primary candidate evidence uses WikiText-2 real local split files with
fallback disabled. 3B adds real HuggingFace streaming samples for OpenWebText
and C4 English as cross-dataset audit evidence.

- Dataset key: `wikitext2_paper`
- dataset_status: `real_local_nonfallback` in the manifest and accepted as real non-fallback
- dataset_scope: `official_split`
- Manifest: `artifacts/data/wikitext2_paper/data_manifest.json`

3B streaming-sample datasets:

- `openwebtext_streaming`: `real_nonfallback`, `streaming_sample`
- `c4_en_streaming`: `real_nonfallback`, `streaming_sample`

These are bounded streaming samples, not complete upstream corpus runs.

## Baselines

- `raw`: no filtering
- `random_same_keep_rate`: seeded random retention
- `dedup_only`: exact deduplication only
- `length_filter`: longest-document retention baseline
- `hdqspp`: HDQS++ v1
- `hdqspp_v2`: distribution-preserving v2 candidate
- `hdqspp_v3`: calibrated audit candidate

## Fairness Controls

Candidate rows share tokenizer hash, vocabulary size, parameter count, training
token budget, and evaluated validation token budget. The purity check is:

```bash
python scripts/check_main_results_purity.py
```

## Training Budget

- train_tokens: `1228800`
- evaluated_validation_tokens: `53248`
- model size: `small`
- seeds: `1 2 3`

3B streaming dev runs use the same `small` model and seed list, but a smaller
dev budget recorded in `configs/experiments/openwebtext_dev.yaml` and
`configs/experiments/c4_en_dev.yaml`. They are cross-dataset audit rows, not
paper-scale claims.

## Evaluation

The primary model metric is final validation perplexity on the WikiText-2 dev
split. Lower is better. Test split is not used for method selection.

## Significance Protocol

With 3 seeds, comparisons are preliminary. CI-crossing-zero results are
`trend_only`, not supported claims.

## Main Results Purity

`main_results` is rebuilt from `completed_training` registry rows only.
`method_debug`, filtering-only rows, failed rows, and configured-not-run rows do
not enter the primary table.

Streaming-sample rows are reported separately in:

- `artifacts/cross_dataset/cross_dataset_results.csv`
- `artifacts/cross_dataset/dataset_status_matrix.csv`
- `docs/CROSS_DATASET_AUDIT.md`

## Method Status

Primary method status is `honest_audit_framework`. The secondary finding is
`hdqspp_v3_improves_over_v2_trend_but_not_raw`.
