# Benchmark Card

## Name

LLM Data Quality Benchmark

## Intended Use

Reproducible research-prototype experiments for data-quality interventions in
small-scale language-model pretraining.

## Primary Evidence

Run `python scripts/run_quick_experiment.py`, then inspect
`artifacts/quick_experiment/REPORT.md`. Quick mode is single-seed smoke-test
evidence. See `docs/LIMITATIONS.md` before describing results.

## Auxiliary Measurement

Attention throughput is a hardware-dependent supporting benchmark. CPU
working-set values are estimates; PyTorch SDPA is not introduced as a novel
algorithm.
