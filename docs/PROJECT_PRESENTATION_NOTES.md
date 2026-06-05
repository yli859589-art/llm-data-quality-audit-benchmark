# Project Presentation Notes

## Opening

This is a negative-result audit benchmark for LLM data-quality filtering. The
core question is: can a plausible data-quality filter fail under fair training
controls? In this release, yes.

## Main Narrative

1. Data filtering is tempting because proxy metrics look clean.
2. Fair evaluation requires raw, random, and dedup baselines.
3. The benchmark uses real data, shared tokenizer/model budgets, split checks,
   append-only registry, and artifact lineage.
4. HDQS++ v3 improves over v2 trend-wise, but not over raw.
5. The value is a reproducible audit system, not a claimed winning filter.

## Key Sentence

HDQS++ v3 does not outperform raw under the current fair benchmark.

## What To Show

- `PROJECT_ONE_PAGE.md`
- `artifacts/tables/main_results.csv`
- `docs/CROSS_DATASET_AUDIT.md`
- `docs/FIGURE_INDEX.md`
- `artifacts/release/final_release_report.md`

## Common Questions

**Is this a method-success project?**  
No. It is an audit benchmark showing why method claims need fair baselines.

**Are OpenWebText/C4 full benchmarks?**  
No. They are real streaming samples.

**Why is a negative result useful?**  
Because it prevents unverified filters from being treated as improvements.

## Closing

The project is ready as a GitHub release candidate and portfolio benchmark. It
is not a paper-ready or CCF-C-ready artifact.
