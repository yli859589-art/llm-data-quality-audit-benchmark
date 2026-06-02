# Resume-Safe Project Description

## Recommended title

**LLM Data Quality and Efficient Attention Benchmark Platform** | Python, PyTorch, NumPy

## Recommended bullets

- Built a reproducible LLM data-quality benchmark on the public Tiny Shakespeare corpus, comparing raw data with cleaning, PII redaction, deduplication, quality-filter, and full-pipeline ablations.
- Reduced duplicate rate from `9.0%` to `0`, removed all injected email and phone hits, and lowered held-out character-level GPT perplexity from `40.14` to `36.00` (`10.29%`) in a deterministic stress test.
- Benchmarked naive, numerically stable online-reference, and PyTorch SDPA attention implementations; measured `3.77x` SDPA throughput at sequence length `128` with an estimated `50.0%` smaller algorithmic working set.
- Added `20` numerical and regression tests, `92%` source coverage, checksum-verified public data, SVG visualizations, cross-platform verification scripts, and GitHub Actions CI.

## Supporting-suite description

Implemented compact reference algorithms across search, reinforcement learning, probabilistic inference, classical ML, differentiable layers, NLP, and LLM systems foundations.

## Phrases to avoid

Do not describe this project as:

- `CMU course competition submission` unless an instructor accepted it for that purpose.
- `Stanford/Berkeley official coursework completion`.
- `Official grader pass`, `leaderboard placement`, or `state-of-the-art model`.

Use `personal LLM systems benchmark` and `public-course-inspired supporting implementation suite`.
