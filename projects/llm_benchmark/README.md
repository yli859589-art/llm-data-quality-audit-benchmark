# LLM Data Quality and Efficient Attention Benchmark Platform

This is the repository's focused portfolio project. It benchmarks data-quality controls and attention implementations using a checksum-verified public Tiny Shakespeare corpus.

## Research question

How much do deterministic data-quality controls improve compact GPT training, and how do attention implementations compare on correctness, throughput, and estimated memory?

## Reproduce

```bash
python scripts/run_llm_benchmark.py
```

## Artifacts

- `artifacts/llm_benchmark/REPORT.md`
- `artifacts/llm_benchmark/results.json`
- `artifacts/llm_benchmark/training_curves.svg`
- `artifacts/llm_benchmark/attention_throughput.svg`

## Scope

The public corpus is real. Noise injection is a deterministic stress test. Results are local CPU measurements, not official leaderboard scores.
