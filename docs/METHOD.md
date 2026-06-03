# Method

## Overview

The project studies data-quality interventions for small-scale language-model
pretraining. It is a research prototype: the method pipeline, baselines,
statistics, and artifacts are implemented, but current quick and
paper-prototype results remain preliminary.

The benchmark separates three evidence levels:

- `quick`: reproducibility and instrumentation smoke test.
- `paper-prototype`: executable local small-run matrix plus remote fallback records.
- `full`: future large-dataset, longer-training mode required for paper claims.

## Data-Quality Intervention Pipeline

The default full pipeline is:

```text
raw documents
  -> controlled/pseudo-real noise injection
  -> text cleaning
  -> synthetic PII redaction
  -> exact deduplication
  -> MinHash-LSH near deduplication
  -> HDQS++ scoring
  -> retention-aware quality filtering
  -> equal-budget Mini GPT training/evaluation
```

Pipeline-order artifacts compare alternate orderings, but those rows are
preprocessing diagnostics unless a later experiment explicitly trains each
order.

## Noise Modeling

Controlled synthetic noise includes HTML boilerplate, URL spam, synthetic PII
canaries, exact duplicates, near duplicates, OCR-like corruption, mojibake,
repeated n-grams, low-information templates, mixed language, excessive symbols,
and generated-like repetition.

Pseudo-real web noise adds navigation bars, footer copyright text, SEO keyword
stuffing, ad blocks, cookie banners, malformed HTML, boilerplate templates,
multilingual fragments, encoding artifacts, low-information pages, and
repeated template pages.

These stress tests are deterministic and seed-controlled. They do not estimate
the true prevalence of web-corpus noise.

## PII Redaction And Synthetic Canaries

The privacy component uses synthetic canaries only. It detects email-like,
phone-like, and ID-like strings before and after processing, then reports
residual hits, recall, precision, false-positive proxy behavior, and utility
metrics where model runs exist.

This is not a formal privacy audit, membership-inference test, or guarantee for
real private data.

## Exact Deduplication

Exact deduplication hashes full document strings and removes repeated copies
while preserving duplicate-cluster metadata.

## Jaccard Near Deduplication

The Jaccard reference implementation compares token-shingle overlap directly.
It is readable and deterministic, and it acts as a correctness reference for
small cases.

## MinHash-LSH Near Deduplication

The MinHash-LSH path builds deterministic signatures, groups candidates in LSH
buckets, and verifies candidates with exact Jaccard similarity before removal.
It is the scalable near-duplicate path used by the benchmark matrix.

## HDQS++

HDQS++ is a transparent document-quality scoring prototype. Each document is
scored from bounded components:

- lexical diversity
- character entropy
- token entropy
- repetition penalty
- n-gram repetition penalty
- PII density penalty
- URL/HTML noise penalty
- non-linguistic symbol penalty
- length prior
- language consistency
- optional LM surprisal quality
- duplicate-cluster penalty

The implemented score is a weighted average:

```text
score(d) = sum_i weight_i * component_i(d) / sum_i weight_i
```

Current default weights are:

```text
lexical_diversity=1.0
char_entropy=1.0
token_entropy=0.8
repetition_penalty=1.3
ngram_repetition_penalty=1.0
pii_density_penalty=1.2
url_html_noise_penalty=1.0
non_linguistic_symbol_penalty=1.0
length_prior=0.8
language_consistency=0.7
optional_lm_surprisal=0.0
duplicate_cluster_penalty=0.0
```

The HDQS sweep reports threshold and top-k retention behavior. Its
retention-aware diagnostic objective is:

```text
mean_hdqs_retained * document_retention_rate - 0.02 * pii_like_hits
```

This objective discourages extreme filtering and residual PII-like content. It
is a diagnostic proxy, not a tuned paper method. `hdqs_best_config.json` and
`hdqs_failure_cases.md` document the current selection and failure boundaries.

## DQCS Curriculum Selection

DQCS, Data Quality Curriculum Selection, creates deterministic curriculum
orders from HDQS++ scores:

- random
- high-quality-first
- low-quality-first
- easy-to-hard
- hard-to-easy
- quality-stratified
- mixed-quality

Current DQCS artifacts prove that curricula can be generated and compared
reproducibly. They do not prove a stable training gain.

## Pipeline-Order Study

The pipeline-order report compares retained documents, retained characters,
PII-like hits, duplicate counts, and mean HDQS under alternate preprocessing
orders. It helps identify brittle ordering decisions before expensive training.

## Equal-Token-Budget Design

Strict comparison mode trims trained variants to the same shared character
budget. `token_budget_report.json` records the selected budget and per-variant
lengths. Retention-utility tradeoffs are reported separately so retained-data
quantity is not confused with model-quality improvement.

## Multi-Seed Aggregation

Multi-seed aggregation writes seed-level rows, aggregate means, standard
deviations, bootstrap intervals, and paired comparisons when seeds align. The
current paper-prototype seeds are `23`, `42`, and `3407`.

Positive mean improvement means lower perplexity for the candidate, but wide
intervals are reported directly and must not be over-interpreted.

## Privacy-Utility Metrics

Privacy-utility artifacts combine residual PII-like hits, synthetic-canary
removal, retention, held-out perplexity, and next-character accuracy when a
variant was trained. These metrics are useful for engineering tradeoff analysis
but are not a privacy certification.

## Downstream Metrics

Downstream artifacts currently include lightweight proxy tasks such as held-out
next-character accuracy, noisy robustness proxies, and generation-quality
signals. Full downstream NLP evaluation remains future work.

## Attention Benchmark As Auxiliary System Check

The attention benchmark compares readable attention implementations and
PyTorch SDPA across short sequence lengths. It records timing, correctness, and
environment metadata. This is an auxiliary systems sanity check, not the main
research contribution.

## Why This Is Research-Prototype Level

The project has a defined research question, controllable intervention matrix,
baselines, ablations, dataset cards, fallback records, multi-seed statistics,
generated reports, CI, tests, and coverage. That makes it suitable as a
resume-ready and CCF-C-convertible research prototype.

It is not a completed paper because external datasets, longer training,
larger-scale models, fixed method tuning, formal literature review, and
paper-style writing are still required.

## Current Limitations

- Quick and paper-prototype runs are compact.
- Optional public datasets are fallback records unless approved data are provided.
- HDQS++ weights are not tuned on a held-out development split.
- DQCS curriculum gains are not established.
- Synthetic canaries are not a formal privacy audit.
- CPU/GPU timing depends on local hardware and PyTorch kernels.
