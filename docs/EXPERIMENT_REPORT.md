# Reproducible Experiment Report

## Focused project

The repository's primary project is the **LLM Data Quality and Efficient Attention Benchmark Platform**. It uses a checksum-verified Tiny Shakespeare public corpus and writes reproducible artifacts to `artifacts/llm_benchmark/`.

Run:

```bash
python scripts/run_llm_benchmark.py
```

Generated artifacts:

- [`REPORT.md`](../artifacts/llm_benchmark/REPORT.md)
- [`results.json`](../artifacts/llm_benchmark/results.json)
- [`training_curves.svg`](../artifacts/llm_benchmark/training_curves.svg)
- [`attention_throughput.svg`](../artifacts/llm_benchmark/attention_throughput.svg)

## Focused benchmark summary

| Metric | Raw noisy baseline | Full pipeline | Change |
|---|---:|---:|---:|
| Duplicate rate | 9.0% | 0.0% | -9.0 pp |
| Email and phone hits | 48 | 0 | -100% |
| Held-out GPT validation loss | 3.6923 | 3.5837 | -2.94% |
| Held-out GPT perplexity | 40.14 | 36.00 | -10.29% |

At sequence length `128`, PyTorch SDPA achieved `3.77x` the naive reference throughput with an estimated `50.0%` smaller algorithmic working set.

## Supporting implementation checks

Run:

```bash
python scripts/run_experiments.py
python scripts/run_verification.py
```

These commands verify deterministic toy or synthetic checks across the supporting AI/ML implementation families. They are useful implementation evidence but are separate from the focused Tiny Shakespeare experiment.

## Interpretation

The focused benchmark supplies a clear research question, real public text, a baseline, ablations, sanitized error analysis, training curves, and systems measurements. It does not establish production-scale quality, official leaderboard performance, or fitness for a specific course rubric.
