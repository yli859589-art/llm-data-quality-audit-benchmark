# Research Readiness

## Current Research Elements

The project now has the core ingredients of a CCF-C-convertible AI research
prototype:

- a clear research question about data quality under fixed training budgets;
- configurable dataset matrix with offline fallback and dataset cards;
- controlled synthetic and pseudo-real web-noise injection;
- exact, Jaccard, and MinHash-LSH deduplication;
- HDQS++ scoring and DQCS curriculum-selection diagnostics;
- baseline and ablation matrix with retention-matched controls;
- privacy-utility analysis based only on synthetic canaries;
- multi-seed result tables and statistical summaries;
- generated research tables, figures, failure analysis, and project report;
- CI, lint, type checks, tests, coverage, and repository hygiene checks.

## Results Already Run

The committed quick artifacts are CPU-bounded smoke-test evidence. They include
model metrics for selected variants, quality-score distributions, privacy
checks, HDQS sweep diagnostics, pipeline-order diagnostics, curriculum
diagnostics, and dataset-matrix evidence.

The v4.3 paper-prototype artifacts add real lightweight runs on
`tiny_shakespeare`, `mixed_debug`, `synthetic_web_noise`, and
`local_wikitext_sample`, plus fallback-only records for `wikitext2`,
`openwebtext_sample`, and `c4_sample` when local/network data are unavailable.
The multi-seed run uses seeds `23`, `42`, and `3407` and writes paired
comparisons, but the confidence intervals are still wide.

These results are useful for a resume and GitHub portfolio because they show
that the system is executable, reproducible, and instrumented. They are not
paper-level empirical evidence.

## Why It Is CCF-C-Convertible

The project can be converted into a paper-style submission because the method,
experiment matrix, baselines, uncertainty reporting, and artifact pipeline are
already implemented. A future paper can scale the same scripts to larger
datasets and longer training runs without changing the research question.

## Why It Is Not a Completed Paper

The project has not yet run the full explicit-network or local large-dataset
matrix. HDQS++ weights have not been tuned on a separate development split.
Most model evidence is still compact, CPU-oriented, and single-seed or
small-seed. No venue submission, review, acceptance, or publication claim is
made.

## Full Experiment Checklist

Before paper submission:

1. Review usage policies for WikiText-2, OpenWebText, and C4.
2. Replace fallback-only optional public rows with approved local or network
   dataset runs.
3. Run `full` mode with longer training budgets and at least two model scales.
4. Tune HDQS++ weights on a development split, then freeze them.
5. Report confidence intervals and paired comparisons for every trained
   baseline.
6. Add deeper privacy tests beyond synthetic canary redaction if making privacy
   claims.
7. Expand failure analysis with manually categorized, redacted examples.
