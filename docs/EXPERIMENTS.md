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
larger attention matrix. The maintained full entry point is
`scripts/run_dataset_matrix.py --mode full`, which iterates over
`tiny_shakespeare`, `wikitext2`, `openwebtext_sample`, `c4_sample`, and
`mixed_debug`. Optional public datasets require explicit network permission;
offline runs fall back cleanly and record the fallback in each dataset card.

## Required Larger Study

Before a paper-style submission, add explicit-network sampled runs for
WikiText-2, OpenWebText, and C4; tune HDQS thresholds on a separate development
split; run multiple retention ratios; and report uncertainty across seeds.

## HDQS Interpretation

In the quick stress test, standalone HDQS filtering is not consistently better
than the raw noisy baseline. Its current role is best interpreted as a pipeline
component that works together with cleaning, PII redaction, and deduplication
rather than as a standalone performance-improving method.

## Attention Benchmark

Attention is auxiliary. The benchmark includes warmup, median, p25, p75,
correctness error against a naive reference, hardware metadata, and
algorithmic working-set estimates. PyTorch SDPA is an optimized framework
primitive, not a novel method introduced by this prototype.
