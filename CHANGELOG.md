# Changelog

## 4.1.0 - 2026-06-03

- Added a dataset-matrix runner with configurable Tiny Shakespeare, WikiText-2,
  OpenWebText-sample, C4-sample, and mixed-debug dataset entries, including
  offline fallback behavior and portable summary artifacts.
- Added MinHash/LSH near-duplicate detection alongside the deterministic
  Jaccard reference implementation.
- Added HDQS sweep artifacts and interpretation notes so quick runs distinguish
  standalone HDQS behavior from the stronger full cleaning pipeline.
- Expanded tests for dataset loading, dataset-matrix dry runs, MinHash/LSH
  stability, HDQS edge cases, supporting algorithm families, and artifact
  hygiene, raising measured source coverage to `93%`.
- Tightened lint/type/CI scope around the main LLM benchmark modules and
  strengthened repository export checks for cache files, absolute paths,
  unsupported claims, and missing experiment artifacts.
- Expanded the paper draft, resume note, experiment docs, dataset docs, and
  limitations to present the project as a personal research prototype rather
  than official coursework, competition, or publication evidence.

## 4.0.0 - 2026-06-03

- Refocused the repository on data-quality interventions for small-scale
  language-model pretraining.
- Added deterministic 12-family corruption, HDQS scoring, near deduplication,
  equal-budget comparisons, privacy checks, downstream metrics, multi-seed
  support, generated tables, and generated figures.
- Added dataset and model configs, offline fallback behavior, research
  documentation, repository hygiene checks, formatting, linting, typing,
  pre-commit, and CPU-bounded CI.
- Repositioned attention measurements as an auxiliary hardware-dependent
  benchmark with median and interquartile statistics.

## 3.0.0

- Added the focused LLM Data Quality and Efficient Attention Benchmark Platform.
- Added checksum-verified Tiny Shakespeare public data and source attribution.
- Added raw baseline, data-quality ablations, held-out character-level GPT evaluation, error analysis, and SVG charts.
- Added naive, online-reference, and PyTorch SDPA attention benchmarking.
- Expanded tests from 10 to 20 and added a measured 92% source-coverage report.
- Added benchmark, provenance, references, and submission-readiness documentation.

## 2.1.0

- Added supporting AI/ML implementation families, deterministic checks, and portfolio-safe documentation.
