# Technical Overview

This document summarizes the implementation architecture for the audit
benchmark. It follows `docs/REPORTING_CONTRACT.md`; it does not claim that
HDQS++ v3 outperforms raw.

## Data Pipeline

Data configs produce explicit manifests with dataset status, dataset scope,
split hashes, content hashes, token counts, and fallback flags. WikiText-2 is
the primary official-split candidate evidence. OpenWebText and C4 English are
real HuggingFace streaming samples.

## Filtering Methods

The benchmark compares raw, `random_same_keep_rate`, `dedup_only`, length
filtering, HDQS++ v1/v2, and HDQS++ v3 variants. HDQS++ v3 is treated as an
audited candidate, not a supported over-raw method.

## Training Loop

The project runs small GPT-style model training with fixed token budgets,
validation budget tracking, and shared model configuration where required by the
main candidate matrix.

## Tokenizer Fairness

Candidate rows are checked for shared tokenizer hash, vocabulary size, parameter
count, training budget, and evaluated validation-token budget.

## Run Registry

`artifacts/runs/run_registry.jsonl` is append-oriented. Failed and superseded
runs are retained for audit evidence. `run_registry.csv` is regenerated from the
registry for analysis.

## Artifact Lineage

Lineage checks validate artifact hashes, superseded rows, and expected output
paths. This prevents silent result replacement.

## Claim Hygiene

`scripts/check_claim_hygiene.py` scans public-facing documents and separates
unsafe claims from allowed negative, forbidden-claim, and archival contexts.

## Cross-Dataset Audit

`artifacts/cross_dataset/` separates WikiText-2, OpenWebText streaming sample,
and C4 English streaming sample rows. Perplexity should be interpreted within
dataset/tokenizer/model-budget boundaries.

## Release Checks

Release readiness is guarded by:

- `scripts/run_all_checks.py`
- `scripts/run_release_checks.py`
- `scripts/verify_fresh_unzip.py`
- `scripts/check_experiment_readiness.py`

HDQS++ v3 does not outperform raw under the current fair benchmark.
