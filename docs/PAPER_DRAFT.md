# Paper Draft: Data Quality Interventions for Small-Scale Language Model Pretraining

## Abstract

This prototype studies transparent data-quality interventions for small-scale
language-model pretraining. It combines deterministic corruption, PII
redaction, exact and near deduplication, a heuristic document-quality score,
equal-budget comparisons, and generated privacy and utility artifacts. The
checked-in quick experiment is a reproducibility smoke test. Multi-seed and
multi-dataset results remain required before a submission.

## 1. Introduction

Language-model data pipelines often mix cleaning, privacy handling,
deduplication, and quality filtering. This repository isolates those
interventions in a compact, inspectable benchmark so their tradeoffs can be
measured under a shared character budget.

## 2. Method

The method uses 12 independently configurable corruption families, stable
exact hashing, word-shingle Jaccard near deduplication, and HDQS. Full details
are in `docs/METHOD.md`.

## 3. Experimental Setup

The quick run uses local Tiny Shakespeare and one CPU seed. The larger planned
matrix adds three seeds and explicitly sampled public datasets. See
`docs/EXPERIMENTS.md`.

## 4. Preliminary Reproducibility Results

Generated quick tables are written to
`artifacts/quick_experiment/main_results_table.md` and
`artifacts/quick_experiment/ablation_table.md`. They validate execution and
artifact generation; they are not presented as publication-level evidence.

## 5. Auxiliary Systems Measurement

The repository measures naive attention, an online reference, and PyTorch SDPA
using median and interquartile timings. This section is supporting evidence,
not a novel attention-algorithm contribution.

## 6. Limitations and Ethics

The required boundaries are documented in `docs/LIMITATIONS.md` and
`docs/ETHICS.md`.

## 7. Next Experiments

Run a multi-dataset, multi-seed matrix; tune quality thresholds on separate
development data; add BPE-model comparisons; and perform deeper privacy and
language-bias analysis before preparing a venue submission.
