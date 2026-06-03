# Method

## Problem Definition

The prototype studies how data-quality interventions affect small-scale
language-model pretraining under fixed character/token budgets. Controlled
corruption and pseudo-real web noise create reproducible stress tests; they are
not estimates of natural web noise prevalence.

## HDQS++ / DQCS

HDQS++ is a transparent document-quality scoring prototype. Each document
receives component scores for lexical diversity, character entropy, token
entropy, repetition, n-gram repetition, HTML/URL noise, PII density, symbol
noise, language consistency, length prior, optional LM surprisal, and
near-duplicate cluster penalty.

DQCS, or Data Quality Curriculum Selection, builds deterministic curricula
from HDQS++ scores:

- random baseline;
- high-quality-first;
- low-quality-first;
- easy-to-hard;
- hard-to-easy;
- quality-stratified sampling;
- mixed-quality curriculum.

Quick artifacts validate that these curricula can be constructed reproducibly.
They do not claim curriculum training gains until multi-seed model runs are
performed.

## Deduplication

Exact deduplication hashes full document strings. Jaccard near deduplication is
kept as a readable reference. MinHash/LSH produces deterministic signatures and
candidate buckets, then verifies candidates with exact Jaccard similarity
before removal. Duplicate clusters preserve representative/member indices,
thresholds, and method metadata.

## Pipeline Order Study

The pipeline-order study compares deterministic preprocessing outcomes for:

- clean -> redact -> exact dedup -> near dedup -> HDQS;
- clean -> dedup -> redact -> HDQS;
- HDQS -> clean -> dedup;
- redact before dedup;
- redact after dedup;
- near dedup before HDQS;
- near dedup after HDQS.

The output is `pipeline_order_report.json` and
`pipeline_order_comparison.svg`. These rows are preprocessing diagnostics, not
separate model-training claims unless a later experiment explicitly trains
each order.

## Privacy Utility

The privacy component uses synthetic canaries only. It reports detection
before processing, residual canary count, recall, precision, false-positive
rate, redaction side effects, a lightweight exposure-reduction indicator, and
utility metrics such as held-out perplexity and next-character accuracy when a
variant was trained.

This is not a formal privacy audit or safety certification.

## Equal Budget Rule

Strict comparison mode trims every trained variant to the same shared
character budget. `token_budget_report.json` records the selected budget and
per-variant lengths. Unequal retained-data studies are reported separately as
retention/utility tradeoffs.

## Auxiliary Attention Benchmark

Attention measurements include sequence-length sweeps, warmup, median/p25/p75
timing, correctness checks, thread/device/PyTorch metadata, and algorithmic
working-set estimates. They are auxiliary systems checks; SDPA speed is not
claimed as a new algorithmic contribution.
