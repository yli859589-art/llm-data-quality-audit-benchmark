# Project Summary

## One-Sentence Introduction

LLM Data Quality Diagnostics and Risk Auditing Benchmark is a reproducible
benchmark for testing whether LLM data-quality filters actually help under fair
tokenizer, model, validation, and artifact-lineage controls.

## Background Problem

LLM pretraining pipelines often assume that heuristic quality filtering improves
data. This project audits that assumption. It asks whether filters that look
reasonable by proxy metrics still help when compared against raw,
`random_same_keep_rate`, and `dedup_only` baselines under the same training
budget.

## Why LLM Data Quality Filtering Needs Auditing

Filtering can silently harm validation perplexity by over-removing useful text,
changing distribution shape, or optimizing proxy diagnostics that do not
translate into model loss. The project is valuable because it preserves those
negative findings instead of hiding them.

HDQS++ v3 does not outperform raw under the current fair benchmark.

## System Architecture

- Data preparation with explicit `dataset_status` and `dataset_scope`
- Real non-fallback WikiText-2 official split evidence
- Real OpenWebText/C4 HuggingFace streaming-sample audit evidence
- Filtering methods: raw, random same keep-rate, dedup, HDQS++ variants
- Small GPT-style training loop with shared tokenizer/model budget
- Append-only run registry
- Artifact lineage and hash checks
- Claim hygiene checks and release gates

## Datasets And Methods

- `wikitext2_paper`: `real_local_nonfallback`, `official_split`
- `openwebtext_streaming`: `real_nonfallback`, `streaming_sample`
- `c4_en_streaming`: `real_nonfallback`, `streaming_sample`

OpenWebText and C4 are streaming samples, not complete upstream dataset runs.

## Benchmark Protocol

The primary candidate matrix uses a `small` model, 3 seeds, shared tokenizer,
shared vocabulary, shared parameter count, fixed training tokens, split-integrity
checks, and no-test-leakage validation. Cross-dataset rows are reported
separately from `main_results.csv`.

## Key Findings

- Raw is the strongest mean-PPL baseline on the WikiText-2 candidate matrix.
- Dedup and random same keep-rate remain strong comparison baselines.
- HDQS++ v3 improves over HDQS++ v2 trend-wise, but not over raw.
- Cross-dataset streaming samples show the same caution: heuristic filtering can
  be fragile and can underperform raw/dedup baselines.

## Failure Diagnostics

The project treats method failure as evidence. Diagnostics track keep rate,
distribution shift, component ablations, failure cases, and method comparison
confidence intervals so reviewers can see why a filter failed rather than only
seeing the final score.

## Reproducibility Design

- `artifacts/runs/run_registry.jsonl` is append-oriented.
- `artifacts/tables/main_results.csv` is purity-checked.
- `scripts/check_claim_hygiene.py` guards public claims.
- `scripts/verify_fresh_unzip.py` validates release zips from a clean extraction.
- `docs/REPORTING_CONTRACT.md` is the source of truth for public wording.

## Limitations

- Current model scale is `small`.
- Current main comparison uses 3 seeds.
- OpenWebText/C4 evidence is streaming-sample evidence only.
- Method improvement over raw is unsupported.
- Held-out test evaluation should only be used after method settings are frozen.

## Roadmap

4A future research enhancement, not executed in this release:

- BPE tokenizer
- medium model
- larger OpenWebText/C4 streaming samples
- stronger baselines
- held-out test evaluation after freezing
- mechanism diagnostics
- medium-scale compute logs
- later paper/competition conversion

This release is a GitHub release candidate for an honest negative-result audit
benchmark, not a new experiment stage.
