# LLM Data Quality Benchmark

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A resume-ready AI research prototype with CCF-C-style experiment
infrastructure scaffolding for studying data-quality interventions in
small-scale language-model pretraining.

## What This Is

This repository is a personal research and portfolio prototype: a personal AI
research prototype and benchmark platform designed to make LLM data-quality
experiments reproducible, auditable, and easy to inspect on GitHub. It is not a
completed paper, not an official coursework submission, and not a competition
result.

It does **not** claim institutional affiliation, official coursework
completion, private-grader access, paper acceptance, publication readiness, or
competition placement.

## Research Question

How do data-quality interventions affect small-scale language-model
pretraining under controlled noise, pseudo-real web noise, fixed token budgets,
and privacy constraints?

## Core Capabilities

- Controlled and pseudo-real web-noise injection
- Synthetic PII canaries and PII redaction
- Exact deduplication, Jaccard near deduplication, and MinHash-LSH near deduplication
- HDQS++ document-quality scoring
- DQCS curriculum-selection diagnostics
- Pipeline-order studies
- Equal-token-budget ablations
- Character-level Mini GPT training
- Dataset matrix and paper-prototype small runs
- Multi-seed statistics and paired comparisons
- Privacy-utility and downstream proxy reports
- Model-scaling artifacts for character and BPE configs
- Auxiliary attention systems sanity check
- Script-generated JSON, CSV, Markdown, and SVG research artifacts
- Real-data manifest, baseline, frozen-protocol, ablation, significance, and
  claim-safety scripts for the next paper-scale experiment phase

## Architecture

```text
raw/local corpus
      |
      v
controlled + pseudo-real noise injection
      |
      v
cleaning + PII redaction + exact/near dedup
      |
      v
HDQS++ scoring -----> DQCS curriculum diagnostics
      |
      v
equal-budget variant builder
      |
      +--> Mini GPT training + validation metrics
      +--> privacy-utility reports
      +--> downstream proxy reports
      +--> attention sanity benchmark
      |
      v
dataset matrix + multi-seed aggregation
      |
      v
research tables, figures, audit reports, resume-safe docs
```

## Quick Start

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -e .
python scripts/check_repo.py --clean
python scripts/run_quick_experiment.py
python scripts/run_dataset_matrix.py --mode paper-prototype
python scripts/run_multi_seed.py --mode paper-prototype
python scripts/check_artifacts.py
```

Full local validation also includes:

```bash
python -m unittest discover -s tests -v
python scripts/run_model_scaling.py --mode quick
python scripts/prepare_real_data.py --config configs/data/wikitext2_smoke.yaml
python scripts/run_baselines.py --config configs/experiments/smoke.yaml
python scripts/freeze_hdqspp.py --config configs/experiments/dev.yaml --dry-run-or-smoke
python scripts/run_ablation.py --config configs/experiments/smoke.yaml
python scripts/analyze_significance.py --input artifacts/runs/run_registry.csv --output artifacts/stats
python scripts/generate_tables.py
python scripts/generate_figures.py
python scripts/check_no_fallback_in_experiments.py
python scripts/check_claims_supported.py
python scripts/check_experiment_readiness.py
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/make_research_tables.py
python scripts/make_research_figures.py
python scripts/analyze_failures.py
python scripts/make_project_report.py
python scripts/run_coverage.py
ruff check .
mypy src/course_project_suite/llm_benchmark
```

`black --check .` is configured for CI. On local CPython 3.12.5, Black may
refuse to run because of its upstream safety guard; see
[FINAL_VERIFICATION_REPORT](docs/FINAL_VERIFICATION_REPORT.md).

## Experiment Modes

- `quick`: CPU-oriented single-seed smoke mode. It validates reproducibility,
  instrumentation, artifact generation, and equal-budget wiring.
- `paper-prototype`: real lightweight small runs for local datasets
  (`tiny_shakespeare`, `mixed_debug`, `synthetic_web_noise`,
  `local_wikitext_sample`) plus explicit fallback records for optional remote
  datasets when local/network data are unavailable.
- `full`: future paper-conversion mode for approved external datasets, longer
  training budgets, more seeds, and larger model scales.
- `smoke/dev/paper/full` experiment configs under `configs/experiments/`:
  smoke/dev can use explicitly labeled local fallback fixtures; paper/full
  configs require real data and disallow fallback.

## Current Verified Status

- Unit tests: `63` passing
- Source coverage: `93%` total
- LLM benchmark type check: `mypy` passes on `16` source files
- Repository hygiene: `python scripts/check_repo.py --clean` passes
- Artifact integrity: `python scripts/check_artifacts.py` passes
- Supporting AI/ML family checks: `6/6` pass
- Current local limitation: Black is blocked by local CPython `3.12.5`, not by
  repository formatting evidence

## Small-Run Interpretation

Quick and paper-prototype results are preliminary. They demonstrate that the
experiment matrix is executable, deterministic, and instrumented. They do not
prove that the full pipeline generally outperforms the raw noisy baseline, and
they do not establish a paper-level performance conclusion.

The current multi-seed paper-prototype artifacts report paired comparisons, but
confidence intervals remain wide. Larger datasets, longer training, frozen
HDQS++ tuning, and more model scales are required before making publication
claims.

## Artifacts

- `artifacts/quick_experiment/`: quick results, token-budget report, privacy
  report, attention benchmark, ablation tables, HDQS sweep, training curves,
  failure cases, project report
- `artifacts/dataset_matrix/`: dataset cards, paper-prototype summary,
  fallback reports, per-dataset result records
- `artifacts/multi_seed/`: seed-level results, aggregate results, paired
  statistical tests, multi-seed summary, seed-variance figure
- `artifacts/model_scaling/`: character/BPE model-scaling summaries and
  scaling curve
- `artifacts/research/`: research tables and figures mirrored for GitHub review
- `artifacts/data/`, `artifacts/baselines/`, `artifacts/runs/`,
  `artifacts/ablations/`, `artifacts/stats/`, `artifacts/tables/`, and
  `artifacts/figures/`: experiment-readiness infrastructure artifacts

## Resume Positioning

**LLM Data Quality Benchmark Platform | Python, PyTorch, NumPy**  
Built a reproducible AI benchmark for studying data-quality interventions in
small-scale language-model pretraining, with HDQS++ scoring, DQCS curriculum
diagnostics, deduplication, privacy-utility analysis, multi-seed statistics,
research artifacts, CI, tests, and coverage reporting.

## Limitations

- Current results are compact quick and paper-prototype runs.
- Optional remote datasets are fallback records unless approved local/network
  data are provided.
- HDQS++ and DQCS are research-prototype methods, not validated final methods.
- Synthetic canaries are not a formal privacy audit.
- Attention timing is an auxiliary systems check and is hardware-dependent.

## What This Project Does Not Claim

- It does not claim a completed CCF-C paper.
- It does not claim readiness for publication.
- It does not claim significant LLM performance improvement.
- It does not claim official university or MOOC coursework completion.
- It does not claim private-grader access or private-grader success.

## Documentation

See [METHOD](docs/METHOD.md), [EXPERIMENTS](docs/EXPERIMENTS.md),
[RESEARCH_READINESS](docs/RESEARCH_READINESS.md),
[FINAL_AUDIT](docs/FINAL_AUDIT.md),
[CCF_C_EXPERIMENT_GAP_AUDIT](docs/CCF_C_EXPERIMENT_GAP_AUDIT.md),
[EXPERIMENT_READINESS_REPORT](docs/EXPERIMENT_READINESS_REPORT.md),
[CLAIM_ARTIFACT_MAP](docs/CLAIM_ARTIFACT_MAP.md),
[LIMITATIONS](docs/LIMITATIONS.md), and [RESUME](docs/RESUME.md).

## Supporting Implementations

The broader `src/course_project_suite/` code contains educational search,
reinforcement learning, classical ML, deep-learning layers, BPE, MiniGPT, DPO,
and systems utilities. These are supporting foundations rather than the main
research contribution.

## License

MIT License. See [LICENSE](LICENSE).
