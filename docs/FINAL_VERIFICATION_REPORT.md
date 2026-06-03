# Final Verification Report

Date: 2026-06-03

Verified package target: `4.3.0`.

This repository is a personal research prototype. It does not claim paper
acceptance, official institutional coursework status, private-grader access, or
competition results.

## Audit Result

The v4.2.0 project was already a strong portfolio prototype, but it still
needed clearer research evidence: quick results could be overread as a quality
claim, paper-prototype mode needed real local small runs, optional remote
dataset fallbacks needed explicit records, and the HDQS++ method needed better
failure/configuration artifacts.

The v4.3.0 pass adds those missing pieces while keeping the claim boundary
honest. It improves experimental instrumentation and research readiness; it is
not presented as a completed paper.

## Changes Completed

- Reframed quick-mode results as workflow and instrumentation evidence only.
- Added real paper-prototype small runs for `tiny_shakespeare`, `mixed_debug`,
  `synthetic_web_noise`, and `local_wikitext_sample`.
- Added fallback-only records for `wikitext2`, `openwebtext_sample`, and
  `c4_sample` when local/network data are unavailable.
- Added required per-dataset cards and fallback reports with source, license
  note, fallback, raw/retained characters, retention rate, number of documents,
  seed, token budget, variants, runtime, and command.
- Added three-seed paper-prototype statistics, requested paired comparisons,
  and multi-seed summary artifacts.
- Added pseudo-real web-noise toggles, model-scaling artifacts, HDQS
  best-config reporting, HDQS failure cases, HDQS sweep heatmap, and
  privacy-retention Pareto figure.
- Fixed resume-safe Chinese documentation and updated README, METHOD,
  EXPERIMENTS, DATASETS, REPRODUCIBILITY, RESEARCH_READINESS, LIMITATIONS, and
  internal audit docs.

## Verified Commands

| Command | Result |
| --- | --- |
| `python scripts/run_quick_experiment.py` | Passed |
| `python scripts/tune_hdqs_quick.py` | Passed |
| `python scripts/run_dataset_matrix.py --mode quick` | Passed |
| `python scripts/run_dataset_matrix.py --mode paper-prototype` | Passed |
| `python scripts/run_multi_seed.py --mode paper-prototype` | Passed |
| `python scripts/run_model_scaling.py` | Passed |
| `python scripts/make_tables.py` | Passed |
| `python scripts/make_figures.py` | Passed |
| `python scripts/statistical_analysis.py` | Passed |
| `python scripts/make_research_tables.py` | Passed |
| `python scripts/make_research_figures.py` | Passed |
| `python scripts/analyze_failures.py` | Passed |
| `python scripts/make_project_report.py` | Passed |
| `python scripts/check_artifacts.py` | Passed |
| `python -m unittest discover -s tests -v` | Passed: `63` tests |
| `ruff check .` | Passed |
| `mypy src/course_project_suite/llm_benchmark` | Passed: `16` source files |
| `python -m compileall -q src scripts tests all_course_projects.py` | Passed |
| `python all_course_projects.py --self-check --json` | Passed: `6/6` supporting project families |
| `python scripts/run_coverage.py` | Passed: `93%` total source coverage |
| `black --check .` | Blocked locally by CPython `3.12.5` Black safety guard |

The local sandbox blocks Python `TemporaryDirectory()` writes unless tests run
with an approved writable temp context. Direct unittest and coverage runs were
therefore verified with that environment issue removed.

## Quick Evidence

Quick mode is CPU-oriented, offline, and single-seed (`23`). It is
reproducibility and systems evidence, not paper-level empirical evidence.

| Item | Generated result |
| --- | ---: |
| Shared training-character budget | `18,000` |
| Raw noisy documents | `102` |
| Full-pipeline retained documents | `58` |
| Raw PII-like hits | `39` |
| Full-pipeline PII-like hits | `0` |
| Full-pipeline retention rate | `0.5660` |
| Raw held-out perplexity | `581636.83` |
| HDQS-only held-out perplexity | `604081.16` |
| Full-pipeline held-out perplexity | `559217.60` |

In this quick run, the full pipeline has lower perplexity than the raw noisy
baseline, while HDQS-only is worse than raw. Because this is one compact
short-training run, it is intentionally reported as instrumentation evidence,
not as proof of a stable model-quality improvement.

## Paper-Prototype Dataset Matrix

`python scripts/run_dataset_matrix.py --mode paper-prototype` produced real
small runs for four local datasets and fallback records for optional remote
datasets:

| Dataset key | Fallback | Status |
| --- | ---: | --- |
| `tiny_shakespeare` | False | `paper_prototype_small_run` |
| `mixed_debug` | False | `paper_prototype_small_run` |
| `synthetic_web_noise` | False | `paper_prototype_small_run` |
| `local_wikitext_sample` | False | `paper_prototype_small_run` |
| `wikitext2` | True | `fallback_recorded` |
| `openwebtext_sample` | True | `fallback_recorded` |
| `c4_sample` | True | `fallback_recorded` |

Fallback rows do not claim remote-dataset training. They only document why the
optional dataset was not loaded and which offline fallback was used.

## Multi-Seed Evidence

`python scripts/run_multi_seed.py --mode paper-prototype` ran seeds `23`, `42`,
and `3407` with raw, HDQS, HDQS curriculum, full-pipeline, and
full-without-HDQS variants.

The paired comparisons have favorable mean directions for the candidate
variants, but the confidence intervals are wide and include non-improving
regions. These results are useful for research-readiness evidence, not final
paper claims.

## Black Environment Note

`black --check .` is configured in CI and pre-commit with Black `25.1.0`.
The local machine uses CPython `3.12.5`; Black refuses to run on that
interpreter because of its upstream AST safety warning. This verification
records the block instead of claiming a pass.

## Remaining Work For Paper Conversion

1. Run explicit-network or local WikiText-2, OpenWebText, and C4 samples after
   reviewing dataset policies.
2. Tune HDQS++ weights on a held-out development split, then freeze them.
3. Run full-mode multi-seed training with longer budgets and at least two model
   scales.
4. Report confidence intervals, paired comparisons, and failure categories for
   every trained baseline.
5. Add deeper privacy and memorization evaluations before making privacy
   claims beyond synthetic-canary redaction.

## Deliverable Scope

The repository is ready to present as a resume-ready and CCF-C-convertible LLM
data-quality benchmark research prototype. It is not a completed CCF-C paper,
not ready-for-publication evidence, and not official coursework.
