# Paper Notes

## Candidate Title

Auditable Data-Quality Interventions for Small-Scale Language-Model
Pretraining: Infrastructure, Baselines, and Claim-Safety Checks

## Research Question

Do transparent data-quality filters improve small language-model pretraining
when compared against raw, random, length, heuristic, dedup-only, and proxy
quality baselines under equal token budgets?

## Minimal Paper Experiment

- Datasets: WikiText-2, OpenWebText sample, C4 English sample.
- Modes: dev for threshold selection, paper for final held-out reporting.
- Models: tiny for smoke, small for paper candidate, medium for optional full.
- Seeds: at least five for paper claims.
- Metrics: validation loss, perplexity, retention, PII residuals, duplicate
  removal, training throughput, memory, and failure-case categories.
- Required artifacts: data manifests, frozen HDQS++ config, run registry,
  baseline tables, ablation tables, bootstrap CIs, effect sizes, figures, and
  claim-safety report.

## Non-Claims

The current checked-in smoke/dev artifacts do not prove general LLM
performance improvement and should not be written as final paper results.
