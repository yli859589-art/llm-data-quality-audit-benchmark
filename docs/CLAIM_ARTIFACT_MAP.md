# Claim Artifact Map

Date: 2026-06-04

This map is deliberately conservative. Support level is tied to concrete artifacts.

## Supported Claims

| Claim | Primary artifacts | Support level |
|---|---|---|
| WikiText-2 real local official splits are used with fallback disabled. | `artifacts/data/wikitext2_paper/data_manifest.json`; `artifacts/data/wikitext2_paper/split_integrity_report.json` | Dataset evidence supported |
| Candidate training rows use shared tokenizer/vocab/parameter count and the same token budget. | `artifacts/tables/main_results.csv`; `scripts/check_main_results_purity.py` | Fair-comparison evidence supported |
| Promising variants were selected from Stage 2.5 ablation evidence. | `artifacts/methods/promising_variants.csv`; `scripts/select_promising_variants.py` | Diagnostic selection evidence |
| HDQS++ v3 was frozen from dev evidence without test-split tuning. | `artifacts/methods/hdqspp_v3_design.json`; `configs/frozen/hdqspp_v3_frozen_wikitext2.yaml` | Protocol evidence supported |
| Method-quality claims are preliminary or unsupported depending on the generated status report. | `artifacts/stats/method_status_report.md`; `artifacts/stats/method_comparison_summary.csv` | No overclaim |

## Unsupported Claims

| Claim | Why unsupported |
|---|---|
| HDQS++ is statistically better than raw. | This phase uses 3 seeds and does not permit strong statistical claims. |
| The project is ready for paper submission. | Broader datasets, scales, test evaluation after freezing, and external review artifacts remain incomplete. |
| The project is an official university course or competition submission. | No rubric, policy, registration, or official evaluation record is included. |
