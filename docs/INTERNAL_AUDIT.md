# Internal Audit: v4.3 Research Evidence Upgrade

Date: 2026-06-03

This audit was performed on top of the v4.2.0 repository. It records the
remaining research-evidence gaps and what this pass changed.

## Confirmed Existing Functions

- Main project framing around LLM data-quality benchmarking.
- Dataset adapters for Tiny Shakespeare, WikiText-2, OpenWebText sample, C4
  sample, and mixed debug.
- Quick experiment, dataset matrix, multi-seed script, HDQS sweep script,
  table/figure generation, artifact checks, coverage script, CI, ruff, mypy,
  and pre-commit configuration.
- Exact deduplication, Jaccard near deduplication, and MinHash/LSH near
  deduplication.
- Controlled noise families, privacy canary report, equal-budget character LM
  training, attention benchmark, generated quick artifacts, and broad tests.

## Confirmed Gaps

- Some quick-result wording could still be read as a model-quality claim.
- `paper-prototype` was not yet a real local small-run path for multiple
  datasets.
- Optional public dataset fallbacks needed clearer per-dataset records.
- Multi-seed statistics needed the requested paired comparisons and honest
  interpretation of unstable intervals.
- HDQS++ needed stronger method artifacts: best diagnostic config, failure
  cases, retention-aware objective, and generated figures.
- Pseudo-real web-noise controls and model-scaling artifacts needed to be
  surfaced in code, artifacts, CI, and docs.
- Resume Chinese text had mojibake from an earlier encoding issue.

## Changes Made In This Pass

- Reframed quick results as reproducibility and instrumentation evidence, not
  paper-level model-quality evidence.
- Added real paper-prototype small runs for `tiny_shakespeare`, `mixed_debug`,
  `synthetic_web_noise`, and `local_wikitext_sample`.
- Added fallback-only records for `wikitext2`, `openwebtext_sample`, and
  `c4_sample` when local/network data are unavailable.
- Added per-dataset `fallback_report.json`, paper-prototype summaries, and
  required dataset-card fields for seed, token budget, variants, command, and
  runtime.
- Expanded multi-seed paper-prototype outputs with seed-level results,
  aggregates, paired comparisons, and a generated summary.
- Added pseudo-real web-noise toggles, model-scaling artifact generation, HDQS
  best-config and failure-case artifacts, HDQS heatmap, and privacy-retention
  Pareto figure.
- Updated README, METHOD, EXPERIMENTS, DATASETS, REPRODUCIBILITY,
  RESEARCH_READINESS, LIMITATIONS, RESUME, and final verification docs.

## Not Changed

- The project is still not presented as a completed paper or official course
  result.
- Full public-data training is not run by default because dataset-policy review
  and user-approved network access are required.
- Attention remains auxiliary and is not framed as the main contribution.
