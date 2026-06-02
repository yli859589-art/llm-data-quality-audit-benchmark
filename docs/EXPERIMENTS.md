# Experiments

## Quick CPU Experiment

Run:

```bash
python scripts/run_quick_experiment.py
python scripts/make_tables.py
python scripts/make_figures.py
python scripts/check_artifacts.py
```

Quick mode uses local Tiny Shakespeare, one seed (`23`), a compact training
budget, and no network downloads. Its purpose is reproducibility and pipeline
smoke testing.

## Full Local Experiment

Run:

```bash
python scripts/run_full_experiment.py
```

Full local mode uses seeds `23`, `42`, and `3407`, more training steps, and a
larger attention matrix. It reports mean, standard deviation, and a normal
approximation confidence interval when multiple seeds exist.

## Required Larger Study

Before a paper-style submission, add explicit-network sampled runs for
WikiText-2, OpenWebText, and C4; tune HDQS thresholds on a separate development
split; run multiple retention ratios; and report uncertainty across seeds.

## Attention Benchmark

Attention is auxiliary. The benchmark includes warmup, median, p25, p75,
correctness error against a naive reference, hardware metadata, and
algorithmic working-set estimates. PyTorch SDPA is an optimized framework
primitive, not a novel method introduced by this prototype.
