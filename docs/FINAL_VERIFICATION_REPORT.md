# Final Verification Report

Date: 2026-06-03

This repository is a personal research prototype. It does not claim paper
acceptance, official institutional coursework status, or competition results.

## Verified Commands

| Command | Result |
| --- | --- |
| `python scripts/run_quick_experiment.py` | Passed; generated reproducible quick artifacts |
| `python scripts/make_tables.py` | Passed |
| `python scripts/make_figures.py` | Passed |
| `python scripts/check_artifacts.py` | Passed |
| `python scripts/check_repo.py` | Passed |
| `python -m pytest tests -q` | Passed: `27` tests |
| `ruff check .` | Passed |
| `ruff format --check .` | Passed: `42` Python files already formatted |
| `mypy src` | Passed: `52` source files |
| `python -m py_compile ...` | Passed for source, script, and test files |
| `python scripts/run_coverage.py` | Passed: `91%` measured source coverage |

## Black Environment Note

`black --check .` is configured in CI and pre-commit with Black `25.1.0`.
The local machine uses CPython `3.12.5`; Black intentionally refuses to run on
that interpreter because of its upstream AST safety warning. GitHub Actions
uses Python `3.10`, where the configured standard check remains active. Local
format compatibility was checked with `ruff format --check .`.

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
| Full-pipeline held-out perplexity | `219024.40` |

In this compact smoke test, full-pipeline perplexity is approximately `3.1%`
lower than the raw noisy baseline. The result must be validated with the larger
matrix before it is presented as a research conclusion.

At auxiliary attention sequence length `64`, the generated local CPU artifact
reports PyTorch SDPA at approximately `2.50x` the naive reference throughput
with an estimated `33.3%` smaller algorithmic working set. These values are
hardware-dependent. Estimated CPU working-set values are not measured peak
memory.

## Required Larger Experiments

Before describing this as a CCF-C-style paper prototype suitable for venue
submission:

1. Run the three-seed full matrix with seeds `23`, `42`, and `3407`.
2. Add explicit-network sampled WikiText-2, OpenWebText, and C4 runs after
   reviewing each upstream dataset card and usage policy.
3. Tune HDQS weights and thresholds on a separate development split.
4. Add retention-ratio sweeps, BPE-model comparisons, and deeper privacy and
   language-bias analysis.
5. Report multi-seed mean, standard deviation, confidence intervals, and
   failure-case analysis from the generated artifacts.
