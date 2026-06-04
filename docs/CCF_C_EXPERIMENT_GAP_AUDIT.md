# CCF-C Experiment Gap Audit

## Verdict

This repository is now stronger than a normal personal portfolio project: it
has runnable smoke/dev infrastructure for data manifests, baselines, frozen
HDQS++ protocol generation, ablations, statistics, tables, figures, and claim
checks. It is still not a completed CCF-C-level empirical paper because the
required non-fallback real-data training runs have not been executed.

## Hard Gaps

- Real public corpora have configuration support, but the checked-in verified
  artifacts still use smoke fixtures or existing local small datasets.
- Paper/full configs prohibit fallback; therefore they will fail clearly if
  WikiText-2, OpenWebText, or C4 are unavailable locally.
- Baselines are implemented and comparable at the data-filter level, but
  model-quality comparisons still require multi-seed validation/perplexity
  runs on real corpora.
- HDQS++ can now be frozen with deterministic train/dev/test hashes, but the
  paper templates remain unexecuted until real data is prepared.
- Statistical analysis is claim-safe: it reports unsupported or trend-only
  rows when seed count or model metrics are insufficient.
- The project has generated artifacts, tests, coverage, ruff, and mypy
  evidence, but local Black remains blocked by the upstream CPython 3.12.5
  safety guard documented in the verification report.

## Implemented Infrastructure

- `configs/data/*`: smoke and paper configs for WikiText-2, OpenWebText, and C4
  English.
- `scripts/prepare_real_data.py`: dataset loading, deterministic split, SHA-256
  manifest, provenance, and fallback labeling.
- `scripts/run_baselines.py`: raw, random, length, C4/Gopher-style heuristic,
  dedup-only, n-gram proxy, independent score, and optional wrapper baseline.
- `scripts/freeze_hdqspp.py`: deterministic frozen protocol with split hashes.
- `scripts/run_ablation.py`: HDQS++ component ablation artifacts.
- `scripts/analyze_significance.py`: bootstrap intervals and claim-safety
  reporting when enough rows exist.
- `scripts/check_no_fallback_in_experiments.py`: hard guard against paper/full
  fallback leakage.
- `scripts/check_claims_supported.py`: documentation overclaim guard.
- `scripts/check_experiment_readiness.py`: readiness level report.

## Current Readiness Target

The realistic current label is `PROTOTYPE` after smoke artifacts are generated.
It may become `EXPERIMENT-CANDIDATE` only after at least one real non-fallback
manifest and corresponding baseline/statistical artifacts are created. It must
not be labeled `CCF_C_EXPERIMENT_READY` until all paper-scale data, model,
ablation, significance, and failure-analysis requirements are complete.
