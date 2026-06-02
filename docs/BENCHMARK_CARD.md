# Benchmark Card

## Name

LLM Data Quality and Efficient Attention Benchmark Platform

## Purpose

Measure how deterministic data-quality controls affect compact character-level GPT training and compare readable attention implementations on correctness, throughput, and estimated memory.

## Dataset

- Tiny Shakespeare public corpus.
- Source and SHA-256: [`data/tinyshakespeare/SOURCE.md`](../data/tinyshakespeare/SOURCE.md).
- Training subset: early corpus chunks with deterministic injected stress-test noise.
- Validation subset: clean held-out text from the end of the corpus.

## Baseline and ablations

- `raw_noisy_baseline`
- `clean_redact`
- `deduplicate_only`
- `quality_filter_only`
- `full_pipeline`

Language-model training is reported for the raw baseline, cleaning/redaction ablation, and full pipeline. Data-quality metrics are reported for all variants.

## Metrics

- Duplicate rate, PII hits, quality-filter pass rate, and retained characters.
- Held-out validation loss and perplexity.
- Attention query tokens per second and maximum absolute error against the naive reference.
- Estimated algorithmic working-set bytes and CUDA peak allocation when available.

## Intended use

- Portfolio demonstration.
- Local reproducibility exercise.
- Starting point for a rubric-specific course project after instructor approval.

## Out-of-scope use

- Production corpus certification.
- Claims about natural web-noise prevalence.
- State-of-the-art model evaluation.
- Official leaderboard or institutional certification claims.
