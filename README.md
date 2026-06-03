# LLM Data Quality Benchmark

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Resume-ready and CCF-C-convertible research prototype for **LLM data-quality
benchmarking**. The central question is:

> How do data-quality interventions affect small-scale language-model
> pretraining under controlled noise, pseudo-real web noise, fixed token
> budgets, and privacy constraints?

The primary contribution is an auditable experiment system: deterministic
noise injection, exact/Jaccard/MinHash-LSH deduplication, HDQS++ document
quality scoring, DQCS curriculum selection, pipeline-order studies,
privacy-utility analysis, equal-budget model training, dataset-matrix runners,
multi-seed statistics, and script-generated artifacts. Attention benchmarking
is included only as an auxiliary systems sanity check.

This is a **personal research and portfolio prototype**. It does **not** claim
enrollment at any institution, official coursework completion, competition
placement, private-grader access, paper acceptance, or institutional
affiliation.

## Quick Start

Recommended local setup:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -e .
python -m unittest discover -s tests -v
```

No-install fallback:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

Run the reproducible CPU smoke experiment:

```bash
python scripts/check_repo.py --clean
python scripts/run_quick_experiment.py
python scripts/tune_hdqs_quick.py
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/statistical_analysis.py
python scripts/run_dataset_matrix.py --mode paper-prototype --dry-run
python scripts/make_research_tables.py
python scripts/make_research_figures.py
python scripts/analyze_failures.py
python scripts/make_project_report.py
python scripts/check_artifacts.py
```

Quality gates:

```bash
ruff check .
black --check .
mypy src/course_project_suite/llm_benchmark
python all_course_projects.py --self-check --json
python scripts/run_coverage.py
```

Quick results are single-seed CPU smoke-test evidence. They verify that the
pipeline is reproducible and that the full pipeline behaves better than the
raw noisy baseline in this controlled run. They do not prove a general
model-quality improvement.

## Experiment Modes

- `quick`: local Tiny Shakespeare plus `mixed_debug`, one seed by default,
  offline CPU smoke testing.
- `paper-prototype`: all configured datasets with offline fallback, three
  default seeds for multi-seed runners, and dry-run support for demonstrating
  the future paper experiment matrix without large downloads.
- `full`: longer training and larger dataset matrix. Use only after explicitly
  enabling network access or providing local datasets and reviewing usage
  policies.

Dataset entry point:

```bash
python scripts/run_dataset_matrix.py --mode quick
python scripts/run_dataset_matrix.py --mode paper-prototype --dry-run
python scripts/run_dataset_matrix.py --mode full --allow-network
```

Multi-seed entry point:

```bash
python scripts/run_multi_seed.py --mode quick
python scripts/run_multi_seed.py --mode paper-prototype
```

## Generated Evidence

Core quick artifacts live under `artifacts/quick_experiment/`:

- `main_results_table.md`, `ablation_table.md`, `hdqs_sweep_table.md`
- `curriculum_report.json`, `pipeline_order_report.json`
- `retention_pareto.csv`, `privacy_utility_tradeoff.csv`
- `downstream_results.csv`, `generation_samples.md`
- `seed_level_results.csv`, `aggregated_results.csv`, `statistical_tests.json`
- `privacy_vs_utility.svg`, `pipeline_order_comparison.svg`,
  `model_scaling_curve.svg`, `quality_score_distribution.svg`

Dataset matrix artifacts live under `artifacts/dataset_matrix/`, including
summary CSV/Markdown files and one `dataset_card.json` per dataset entry.

## Method Surface

- Controlled synthetic and pseudo-real web noise: HTML, URLs, PII canaries,
  exact/near duplicates, OCR-like corruption, mojibake, repeated n-grams,
  boilerplate, mixed language, excessive symbols, and generated-like loops.
- Baselines: raw, clean, PII redaction, exact dedup, Jaccard near dedup,
  MinHash-LSH near dedup, rule quality, proxy perplexity filter, HDQS,
  DQCS curriculum, full pipeline, full-pipeline ablations, and retention
  matched baselines.
- HDQS++ components: lexical diversity, character entropy, token entropy,
  repetition, n-gram repetition, HTML/URL noise, PII density, symbol noise,
  language consistency, length prior, optional LM surprisal, and
  near-duplicate cluster penalty.
- Statistics: mean, standard deviation, bootstrap confidence intervals, and
  paired difference summaries when seeds align.

## Documentation

See [METHOD](docs/METHOD.md), [EXPERIMENTS](docs/EXPERIMENTS.md),
[DATASETS](docs/DATASETS.md), [RESEARCH_READINESS](docs/RESEARCH_READINESS.md),
[LIMITATIONS](docs/LIMITATIONS.md), and [RESUME](docs/RESUME.md).

## Supporting Implementations

The broader `src/course_project_suite/` code contains educational search,
reinforcement learning, classical ML, deep-learning layers, BPE, MiniGPT, DPO,
and systems utilities. These are supporting foundations rather than the main
research contribution.

## License

MIT License. See [LICENSE](LICENSE).
