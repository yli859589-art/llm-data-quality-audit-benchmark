# Internal Audit: v4.2 Research Prototype Upgrade

Date: 2026-06-03

This audit was performed before modifying the v4.1.0 repository. It records
what already existed, what was missing, and what this pass changed.

## Confirmed Existing Functions

- Main project framing around LLM data-quality benchmarking.
- Configured dataset adapters for Tiny Shakespeare, WikiText-2, OpenWebText
  sample, C4 sample, and mixed debug.
- Quick experiment, dataset matrix, multi-seed script, HDQS sweep script,
  table/figure generation, artifact checks, coverage script, CI, ruff, mypy,
  and pre-commit configuration.
- Exact deduplication, Jaccard near deduplication, and MinHash/LSH near
  deduplication.
- Controlled noise families, privacy canary report, equal-budget character LM
  training, attention benchmark, generated quick artifacts, and 53+ tests.

## Confirmed Gaps

- README used `pytest` and `mypy src`, while CI used `unittest` and
  `mypy src/course_project_suite/llm_benchmark`.
- There was no `scripts/clean_artifacts.py` and no `check_repo.py --clean`.
- Dataset matrix lacked `paper-prototype` mode and dry-run dataset cards.
- Multi-seed script did not emit seed-level, aggregate, and statistical-test
  artifacts.
- HDQS was not yet documented or artifacted as HDQS++ / DQCS with curriculum,
  pipeline-order, retention, and privacy-utility studies.
- Research tables, research figures, failure analysis, and generated project
  report were not separate reproducible scripts.
- Resume Chinese text had mojibake from an earlier encoding issue.

## Changes Made In This Pass

- Added clean-artifact workflow and integrated `check_repo.py --clean`.
- Added `paper-prototype` dataset mode with offline fallback and dry-run cards.
- Added HDQS++ components, DQCS curriculum diagnostics, pipeline-order study,
  retention Pareto rows, privacy-utility rows, downstream CSV, generation
  samples, and canary memorization report.
- Expanded baselines and added `configs/experiments/baselines.yaml`.
- Added model config entries for char/BPE tiny/small/optional medium variants.
- Added multi-seed statistical outputs and bootstrap/paired-difference helpers.
- Added research table/figure/failure/project-report scripts.
- Updated README, METHOD, EXPERIMENTS, DATASETS, REPRODUCIBILITY,
  RESEARCH_READINESS, LIMITATIONS, RESUME, and final verification docs.

## Not Changed

- The project is still not presented as a completed paper or official course
  result.
- Full public-data training is not run by default because dataset-policy review
  and user-approved network access are required.
- Attention remains auxiliary and is not framed as the main contribution.
