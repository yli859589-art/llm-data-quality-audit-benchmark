# LocalMax CCF-C Candidate Project Report

## Executive Summary

This project is being strengthened from a LocalMax V2 research artifact into a CCF-C-oriented AI research prototype. The target claim is not a paper acceptance claim; it is a project-level claim that the repository contains a reproducible, multi-dataset, multi-baseline audit benchmark for language-model pretraining data filtering under local compute constraints.

Current readiness: `TOP_TIER_CCFC_PROJECT_CANDIDATE`

## Research Question

Do language-model pretraining data filters actually improve language-model utility under controlled token budgets, and when do simple baselines such as length filtering outperform more complex quality selectors?

## Added CCF-C Strengthening Evidence

- Stronger baseline matrix: `raw`, `exact_dedup`, `length_filter`, `random_same_keep_rate`, `c4_quality_filter`, `perplexity_proxy_filter`, `urd_fixed`.
- Target training depth: 5M tokens_seen per run.
- Target matrix: 2 datasets x 7 methods x 3 seeds = 42 runs.
- Metric: per-token validation NLL/log-PPL/PPL with no PPL clipping.
- Downstream: local LAMBADA-style cloze probe only; no official downstream claim.

## Gate Status

| Gate | Passed | Report |
| --- | --- | --- |
| filter_matrix | True | `artifacts/reports/localmax_ccfc_filter_report.json` |
| five_m_training_matrix | True | `artifacts/reports/localmax_ccfc_training_report.json` |
| evaluation_matrix | True | `artifacts/reports/localmax_ccfc_evaluation_report.json` |
| local_downstream_probe | True | `artifacts/reports/localmax_ccfc_downstream_report.json` |

## Current Quantitative Status

- Filter methods completed: `['c4_quality_filter', 'exact_dedup', 'length_filter', 'perplexity_proxy_filter', 'random_same_keep_rate', 'raw', 'urd_fixed']`
- Completed training runs: `42` / `42`
- Best method by valid NLL: `{'c4_en_v2_100m': 'perplexity_proxy_filter', 'openwebtext_v2_100m': 'urd_fixed'}`
- Local cloze probe rows: `8`

## What Would Make This Top-Tier CCF-C Complete

1. Finish all 42 strengthened training runs at >=5M tokens_seen/run.
2. Generate evaluation/statistical tables from the full matrix.
3. Complete local cloze probes for representative methods.
4. Write the final submission-style paper around the honest audit/negative-result finding.

## Claim Hygiene

This report does not claim CCF-C acceptance, CCF-B readiness, Level 3 completion, SOTA, or unsupported URD superiority.
