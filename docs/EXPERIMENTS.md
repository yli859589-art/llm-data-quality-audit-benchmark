# Experiments

## Experiment Modes

### Quick

```bash
python scripts/run_quick_experiment.py
python scripts/run_dataset_matrix.py --mode quick
```

Quick mode is CPU-oriented, offline, and smoke-test sized. It validates
instrumentation, deterministic artifact generation, equal-budget comparisons,
and table/figure generation. It is not model-quality evidence.

### Paper-Prototype

```bash
python scripts/run_dataset_matrix.py --mode paper-prototype
python scripts/run_multi_seed.py --mode paper-prototype
```

Paper-prototype mode runs real lightweight small experiments for local datasets
and records explicit fallback rows for optional remote datasets when local data
or approved network access are unavailable.

### Full

```bash
python scripts/run_dataset_matrix.py --mode full --allow-network
```

Full mode is reserved for future paper conversion. It should be run only after
reviewing upstream dataset policies and deciding compute budgets.

## Dataset Matrix

- `tiny_shakespeare`: local checksum-verified debugging corpus.
- `mixed_debug`: local debug entry for mixed-noise matrix checks.
- `synthetic_web_noise`: local pseudo-real web-noise sample.
- `local_wikitext_sample`: local WikiText-style sample.
- `wikitext2`: optional remote/local dataset; fallback is recorded offline.
- `openwebtext_sample`: optional remote/local dataset; fallback is recorded offline.
- `c4_sample`: optional remote/local dataset; fallback is recorded offline.

Each dataset entry writes `dataset_card.json`, `results.json`, and
`fallback_report.json`. Fallback rows are not treated as remote-dataset
training results.

## Baseline Matrix

The ablation matrix contains:

- `raw_noisy_baseline`
- `clean_only`
- `pii_redact_only`
- `exact_dedup_only`
- `jaccard_near_dedup_only`
- `minhash_lsh_near_dedup_only`
- `rule_quality_filter`
- `proxy_perplexity_filter`
- `hdqs_filter`
- `hdqs_curriculum`
- `full_pipeline`
- `full_pipeline_without_clean`
- `full_pipeline_without_redact`
- `full_pipeline_without_exact_dedup`
- `full_pipeline_without_near_dedup`
- `full_pipeline_without_hdqs`
- `random_retention_matched_baseline`
- `length_matched_baseline`
- `quality_retention_matched_baseline`

Only variants listed in the experiment configuration are trained in a given
run. Other rows are data-processing or retention diagnostics.

## Multi-Seed Design

`paper-prototype` multi-seed mode uses seeds `23`, `42`, and `3407`. It trains
raw, HDQS, HDQS curriculum, full-pipeline, and full-without-HDQS variants under
compact budgets.

Outputs:

- `artifacts/multi_seed/seed_level_results.csv`
- `artifacts/multi_seed/aggregated_results.csv`
- `artifacts/multi_seed/statistical_tests.json`
- `artifacts/multi_seed/multi_seed_summary.md`
- `artifacts/multi_seed/seed_variance.svg`

## Statistical Analysis

The statistics layer reports means, standard deviations, bootstrap confidence
intervals, and paired comparisons where seeds align. Current required paired
comparisons are:

- raw vs full pipeline
- raw vs HDQS
- raw vs HDQS curriculum
- full pipeline vs full pipeline without HDQS

Favorable means are not treated as significant findings when intervals are
wide.

## Model Scaling

```bash
python scripts/run_model_scaling.py --mode quick
```

Model-scaling artifacts summarize configured character and BPE model sizes,
context lengths, and estimated parameter counts. This is config evidence; it
does not claim that every listed model has completed full training.

## Privacy-Utility Evaluation

Privacy-utility artifacts use synthetic canaries and residual PII-like hits.
They report utility metrics such as held-out perplexity and next-character
accuracy when available. They are not a formal privacy certification.

## Downstream Evaluation

Downstream artifacts currently contain lightweight proxy metrics. They provide
smoke-test coverage for evaluation plumbing and should be expanded before paper
submission.

## Attention Benchmark

The attention benchmark records correctness and timing for reference attention
and PyTorch SDPA. It is an auxiliary systems sanity check, not the central
method contribution.

## Artifacts Generated

- `artifacts/quick_experiment/`: quick JSON/CSV/MD/SVG artifacts.
- `artifacts/dataset_matrix/`: dataset cards, fallback reports, summaries.
- `artifacts/multi_seed/`: seed-level and aggregate statistics.
- `artifacts/model_scaling/`: model-scaling summaries and curve.
- `artifacts/research/`: research tables and figures for review.

## Expected Runtime

Quick and paper-prototype modes are designed for local CPU execution. Runtime
depends on PyTorch, thread settings, and device availability. Full mode is not
intended as a default CI job.

## Hardware Notes

CI pins `OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1` for reproducibility. Local
CUDA may be detected, but compact CPU behavior is the expected baseline.

## How To Interpret Current Results

Current quick and paper-prototype results demonstrate that the experiment
matrix is executable and instrumented. They are preliminary and should not be
written as final model-quality conclusions.

## What Remains For Full Paper Conversion

1. Run approved WikiText-2, OpenWebText, and C4 experiments without fallback.
2. Increase training budgets and model scale.
3. Freeze HDQS++ weights after held-out development tuning.
4. Report broader multi-seed statistics and failure categories.
5. Add stronger downstream and privacy evaluations.
6. Write a formal related-work section and paper-style experiment narrative.
