# Final Verification Report

Date: 2026-06-03

Verified package target: `4.1.0`.

This repository is a personal research prototype. It does not claim paper
acceptance, official institutional coursework status, private-grader access, or
competition results.

## Second-Pass Audit Summary

The second-pass review found that the previous package was already a usable
portfolio project, but still needed stronger research evidence and cleaner
export hygiene before it could be described as a high-level
course-competition-style prototype. This revision narrows the claim boundary
and strengthens one main theme: data quality and efficient attention
benchmarking for small-scale language-model pretraining.

Key changes:

- Added a configurable dataset matrix with Tiny Shakespeare, WikiText-2,
  OpenWebText-sample, C4-sample, and mixed-debug entries. Network-backed public
  datasets remain opt-in, with deterministic offline fallback for local checks.
- Added MinHash/LSH near-duplicate detection while keeping exact and Jaccard
  paths as deterministic references.
- Added HDQS sweep reporting and a standalone interpretation note, so quick
  artifacts do not overclaim that HDQS alone improves perplexity.
- Expanded tests around dataset loading, matrix dry runs, near-dedup stability,
  HDQS scoring, selected supporting algorithm edge cases, and artifact hygiene.
- Tightened lint, typing, CI, pre-commit, artifact, and zip-export checks.
- Rewrote resume and paper documentation to avoid official-coursework,
  institution-affiliation, private-grader, competition, or paper-acceptance
  claims.

## Verified Commands

| Command | Result |
| --- | --- |
| `python scripts/run_quick_experiment.py` | Passed; generated reproducible quick artifacts |
| `python scripts/make_tables.py` | Passed |
| `python scripts/make_figures.py` | Passed |
| `python scripts/check_artifacts.py` | Passed |
| `python scripts/run_dataset_matrix.py --mode quick --datasets tiny_shakespeare` | Passed; generated portable dataset-matrix quick artifacts |
| `python -m unittest discover -s tests -v` | Passed: `53` tests |
| `python all_course_projects.py --self-check --json` | Passed: `6/6` project families |
| `ruff check .` | Passed |
| `mypy src/course_project_suite/llm_benchmark` | Passed: `15` main benchmark source files |
| `python -m py_compile ...` | Passed for source, script, and test files |
| `python scripts/run_coverage.py` | Passed: `93%` measured source coverage |
| `python scripts/check_repo.py` | Passed after cache cleanup |

## Black Environment Note

`black --check .` is configured in CI and pre-commit with Black `25.1.0`.
The local machine uses CPython `3.12.5`; Black intentionally refuses to run on
that interpreter because of its upstream AST safety warning. GitHub Actions
uses Python `3.10`, where the configured Black check remains active.

## Generated Quick Evidence

Quick mode is CPU-oriented, offline, and single-seed (`23`). It is a
reproducibility smoke test, not publication-level evidence.

| Item | Generated result |
| --- | ---: |
| Shared training-character budget | `18,000` |
| Raw noisy documents | `93` |
| Full-pipeline retained documents | `56` |
| Exact duplicate removals | `21` |
| Near-duplicate removals after exact deduplication | `10` |
| Raw PII-like hits | `39` |
| Full-pipeline PII-like hits | `0` |
| Synthetic-canary removal recall | `1.0` |
| Synthetic-canary removal precision | `1.0` |
| Raw held-out perplexity | `226073.44` |
| HDQS-only held-out perplexity | `226734.25` |
| Full-pipeline held-out perplexity | `219024.40` |

In this compact smoke test, full-pipeline perplexity is approximately `3.1%`
lower than the raw noisy baseline. The result must be validated with the larger
matrix before it is presented as a research conclusion.

The generated HDQS sweep artifact records that standalone HDQS is not better
than the raw baseline in this quick single-seed run. The current evidence
supports the full pipeline as the stronger intervention, not HDQS alone.

At auxiliary attention sequence length `64`, the generated local CPU artifact
reports PyTorch SDPA at approximately `2.50x` the naive reference throughput
with an estimated `33.3%` smaller algorithmic working set. These values are
hardware-dependent. Estimated CPU working-set values are not measured peak
memory.

## Required Larger Experiments

Before describing this as a venue-submission-level paper prototype:

1. Run the three-seed full matrix with seeds `23`, `42`, and `3407`.
2. Add explicit-network sampled WikiText-2, OpenWebText, and C4 runs after
   reviewing each upstream dataset card and usage policy.
3. Tune HDQS weights and thresholds on a separate development split.
4. Add retention-ratio sweeps, BPE-model comparisons, and deeper privacy and
   language-bias analysis.
5. Report multi-seed mean, standard deviation, confidence intervals, and
   failure-case analysis from the generated artifacts.

## Deliverable Scope

Modified and new files include the main benchmark package, dataset configs,
experiment scripts, tests, generated quick artifacts, generated dataset-matrix
artifacts, CI/pre-commit/tooling files, and research/resume documentation. No
files were intentionally deleted in this pass.

This package is ready to present as a personal LLM data-quality benchmark
prototype on a resume or GitHub. It is not yet evidence for an official course
submission, competition placement, accepted paper, or institution-affiliated
project.
