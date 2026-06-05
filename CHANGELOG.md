# Changelog

## 3C-3-release-candidate-v1 - 2026-06-05

- Added public project display package files for GitHub review, demos,
  presentation notes, figure interpretation, and resume-safe bullets.
- Added final release report generation and required final release artifacts
  under `artifacts/release/`.
- Extended fresh-unzip verification and release checks to require the 3C-3
  display package and final release evidence.
- Preserved `main_results`, cross-dataset results, experiment readiness,
  method status, and append-only registry history.
- Kept 4A as a future roadmap only; no new BPE, medium-model, larger-sample, or
  additional experiment results were added.

## 3C-2-release-candidate - 2026-06-05

- Archived paper, reviewer, submission, and CCF-C gap notes under
  `docs/future_publication_notes/` so they no longer drive the GitHub release
  narrative.
- Added `docs/README.md`, `docs/FRESH_CLONE_TEST.md`, and
  `scripts/verify_fresh_unzip.py`.
- Updated MANIFEST, RELEASE_NOTES, RELEASE_CHECKLIST, and release checks for a
  clean GitHub release-candidate structure.
- Added fresh-unzip verification reports under `artifacts/release/`.
- Preserved all experiment result artifacts, `main_results`, cross-dataset
  results, and append-only registry history.

## 4.5.0 - 2026-06-04

- Added CCF-C-style experiment-readiness infrastructure with explicit
  smoke/dev/paper/full boundaries and no-fallback paper/full guards.
- Added real-data loader scaffolding, deterministic split manifests, SHA-256
  provenance, and smoke fixtures that are labeled as fallback rather than real
  paper evidence.
- Added baseline suite, frozen HDQS++ protocol generation, ablation runner,
  run registry, significance/claim-safety analysis, generated tables, and SVG
  figures.
- Added readiness and claim checks plus reviewer-facing gap audit, attack
  report, claim-artifact map, paper notes, related-work notes, and bibliography.
- Tightened README and resume wording to avoid implying completed paper-level
  or competition-level results.

## 4.4.0 - 2026-06-03

- Added final audit documentation with explicit project positioning, remaining
  limitations, non-claims, and full-experiment conversion checklist.
- Rewrote README, METHOD, EXPERIMENTS, RESEARCH_READINESS, LIMITATIONS, and
  RESUME as final GitHub/resume-facing documentation.
- Added independent `artifacts/research/` tables and figures while preserving
  existing quick-experiment artifact paths.
- Strengthened generated Markdown result tables with mode, seed, budget,
  interpretation, and limitation metadata.
- Strengthened artifact validation across quick, dataset matrix, multi-seed,
  model-scaling, and research artifacts.
- Added multi-seed seed-variance figure generation and made
  `run_model_scaling.py --mode quick` part of the final verification path.

## 4.3.0 - 2026-06-03

- Reframed quick-mode results as workflow and instrumentation evidence only,
  with no claim that quick metrics prove a stable model-quality improvement.
- Added real `paper-prototype` small runs for `tiny_shakespeare`,
  `mixed_debug`, `synthetic_web_noise`, and `local_wikitext_sample`, plus
  explicit fallback records for optional remote dataset entries.
- Added per-dataset fallback reports, paper-prototype summaries, three-seed
  aggregate statistics, paired comparisons, and multi-seed summary artifacts.
- Added pseudo-real web-noise controls, model-scaling artifact generation, HDQS
  best-config reporting, HDQS failure cases, privacy-retention Pareto and HDQS
  sweep heatmap figures.
- Updated documentation, CI smoke commands, artifact checks, resume wording,
  and verification reports for the v4.3 research-prototype scope.

## 4.2.0 - 2026-06-03

- Added `scripts/clean_artifacts.py` and `python scripts/check_repo.py --clean`
  for safe cache cleanup without deleting official quick or dataset-matrix
  artifacts.
- Added dataset-matrix `paper-prototype` mode with offline fallback and dry-run
  dataset cards.
- Expanded HDQS into an HDQS++ / DQCS research prototype with curriculum,
  pipeline-order, retention Pareto, privacy-utility, downstream, generation,
  and statistical artifacts.
- Added broader baseline definitions, model-scale configs, research table and
  figure scripts, failure analysis, generated project report, and
  `docs/RESEARCH_READINESS.md`.
- Unified README, CI, reproducibility, and final verification commands around
  editable install, `unittest`, and `mypy src/course_project_suite/llm_benchmark`.

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
# 3A-release-ready - 2026-06-05

- Rewrote `README.md` as a GitHub-facing audit benchmark entry point.
- Added quickstart, benchmark protocol, artifact index, failure cases, release
  checklist, manifest, release notes, and version metadata.
- Added release entry scripts: `run_all_checks.py`, `run_minimal_benchmark.py`,
  `run_audit_benchmark.py`, `run_release_checks.py`,
  `clean_project_artifacts.py`, and `generate_project_dashboard.py`.
- Added `Makefile` targets for checks, tables, figures, dashboard, and release
  validation.
- Unified primary `method_status` wording to `honest_audit_framework` while
  preserving `hdqspp_v3_improves_over_v2_trend_but_not_raw` as a secondary
  finding.
- No new OpenWebText, C4, medium-model, or HDQS++ v4/v5 experiments were added.
