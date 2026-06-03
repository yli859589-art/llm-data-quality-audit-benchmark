# Method

## Problem Definition

The prototype asks whether auditable data interventions improve small-scale
language-model pretraining when compared under an equal text budget. Controlled
corruption creates a deterministic stress test; it is not an estimate of
naturally occurring web noise.

## Controlled Noise

`noise.py` implements 12 seed-controlled families: HTML boilerplate, URL spam,
PII canaries, exact duplicates, near duplicates, OCR-like corruption,
mojibake, repeated n-grams, low-information templates, mixed-language snippets,
excessive symbols, and generated-like repetition. Each family can be disabled
independently.

## Deduplication

Exact deduplication hashes document strings. The quick experiment uses a
Jaccard word-shingle reference implementation because it is transparent and
easy to audit on small corpora. Larger matrix runs can use MinHash/LSH, which
generates deterministic signatures, buckets them by band, and verifies
candidate pairs before removal. `duplicate_clusters.json` preserves the method,
threshold, representative index, member index, and similarity evidence.

## HDQS

The Heuristic Document Quality Score, abbreviated HDQS or DQScore, is a
transparent score in `[0, 1]`. It is the configurable weighted mean of:

- lexical diversity
- normalized character entropy
- repetition penalty
- PII-density penalty
- URL and HTML-noise penalty
- non-linguistic-symbol penalty
- length prior
- language consistency
- optional duplicate-cluster penalty

The implementation supports threshold filtering and top-k retention ratios.
`quality_scores.csv` preserves per-document scores and components, while
`hdqs_sweep_report.json` records threshold and top-k retention sweeps. In quick
mode, HDQS is treated as a pipeline component rather than a standalone
performance claim.

## Fairness Rule

Strict comparison mode concatenates each selected variant and trims every
training text to the same shared character budget: the minimum of the requested
budget and every retained variant length. `token_budget_report.json` records the
decision. Unequal-budget mode is available only for retention-tradeoff studies
and must not be described as a strict comparison.

## Models

Quick mode trains a character-tokenized decoder-only causal MiniGPT. The
supporting suite also includes a BPE tokenizer. Metrics include held-out loss,
perplexity, bits per character, next-character accuracy, throughput, wall time,
and optional CUDA peak allocation.
