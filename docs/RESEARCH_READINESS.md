# Research Readiness

## Current Research Assets

### Method

- Deterministic controlled and pseudo-real web-noise injection.
- PII redaction with synthetic canaries.
- Exact, Jaccard, and MinHash-LSH deduplication.
- HDQS++ transparent quality scoring.
- DQCS curriculum-selection diagnostics.
- Pipeline-order diagnostics.
- Equal-budget small language-model training.

### Data Matrix

- Local small-run datasets: `tiny_shakespeare`, `mixed_debug`,
  `synthetic_web_noise`, `local_wikitext_sample`.
- Optional public dataset entries: `wikitext2`, `openwebtext_sample`,
  `c4_sample`.
- Fallback reports distinguish unavailable optional datasets from real results.

### Baselines

The project contains raw, cleaning-only, PII-only, exact-dedup-only,
near-dedup-only, quality-filter, HDQS, DQCS, full-pipeline,
full-pipeline-ablation, and retention-matched baselines.

### Multi-Seed

Paper-prototype multi-seed artifacts use seeds `23`, `42`, and `3407` and
report seed-level rows, aggregate rows, paired comparisons, and seed variance.

### Privacy

Privacy artifacts use synthetic canaries and residual PII-like counts. They are
useful for tradeoff analysis but not a formal privacy audit.

### Downstream

Current downstream artifacts are lightweight proxy checks. They validate the
evaluation plumbing and should be expanded for paper conversion.

### Artifacts

The repository generates JSON, CSV, Markdown, and SVG artifacts for quick
experiments, dataset matrix, multi-seed statistics, model scaling, research
tables, research figures, project reports, and failure analysis.

### CI And Tests

The repository includes GitHub Actions, ruff, Black configuration, mypy,
unittest coverage, repository hygiene checks, artifact checks, and supporting
AI/ML family self-checks.

## Current Verified Results

Quick mode has been run as a smoke test and generates model metrics, quality
scores, privacy reports, attention timing, tables, and figures. It should be
read as reproducibility and instrumentation evidence.

Paper-prototype mode has real local small runs for `tiny_shakespeare`,
`mixed_debug`, `synthetic_web_noise`, and `local_wikitext_sample`. It records
fallback-only rows for `wikitext2`, `openwebtext_sample`, and `c4_sample` when
local/network data are not available.

Multi-seed paper-prototype mode has been run for seeds `23`, `42`, and `3407`.
The paired comparisons show directions and variance, but intervals are wide.

## Why The Project Is CCF-C-Convertible

The project is convertible because it already has the research skeleton needed
for a paper-style extension:

- a concrete research question;
- a reproducible intervention pipeline;
- multiple baselines and ablations;
- dataset cards and fallback provenance;
- multi-seed statistics;
- privacy and downstream proxy artifacts;
- failure analysis and generated figures;
- CI, tests, coverage, and repository hygiene gates.

Convertible does not mean completed. It means the codebase can be scaled into a
paper experiment if stronger data, training, tuning, and writing are added.

## What Is Still Missing For An Actual CCF-C Paper

- Full multi-dataset runs without fallback for optional public datasets.
- Longer training budgets.
- Larger model scales.
- Real external dataset results.
- Stronger statistical significance and wider seed coverage.
- Held-out tuning and freezing of HDQS++ weights.
- Stronger downstream tasks and privacy/memorization evaluations.
- Formal literature review and paper writing.

## Risk Assessment

- HDQS++ may be unstable across datasets or longer training.
- Short-run directions may not hold in long-run training.
- Fallback datasets cannot replace true remote-dataset evidence.
- CPU attention and throughput benchmarks are hardware-dependent.
- Synthetic canary privacy checks do not cover real privacy threats.

## Next-Stage Full Experiment Checklist

- [ ] Review dataset licenses and usage policies.
- [ ] Provide local or approved network data for WikiText-2, OpenWebText, and C4.
- [ ] Run a larger externally reviewed dataset matrix without fallback rows.
- [ ] Increase training steps and model sizes.
- [ ] Tune HDQS++ on a development split and freeze it.
- [ ] Run more seeds and report paired intervals.
- [ ] Add stronger downstream tasks.
- [ ] Add stronger privacy and memorization tests.
- [ ] Expand manual failure taxonomy.
- [ ] Write related work and paper-style experiment sections.

## Claims Allowed

- Resume-ready AI project.
- CCF-C-convertible research prototype.
- Reproducible LLM data-quality benchmark platform.
- Paper-prototype small-run evidence.
- Multi-seed diagnostic artifacts.

## Claims Not Allowed

- Completed CCF-C paper.
- Ready-for-submission or ready-for-publication result.
- Significant LLM performance improvement.
- Official course project completion.
- Private-grader access or private-grader success.
