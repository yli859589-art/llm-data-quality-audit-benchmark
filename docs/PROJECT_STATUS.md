# Project Status

Date: 2026-06-05

- Readiness: `EXPERIMENT-CANDIDATE`
- Benchmark scope status: `multi_dataset_audit_candidate`
- Method status: `honest_audit_framework`
- Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`
- `ccf_c_ready`: `false`
- Scope: WikiText-2 official split plus OpenWebText/C4 real streaming samples, `small` model dev budget.
- Reporting contract: `docs/REPORTING_CONTRACT.md`

## Current Result

The candidate matrix now includes raw, random, dedup, HDQS++ v1, HDQS++ v2, the selected v2 no-token-frequency variant, and HDQS++ v3.

- raw mean PPL: `12.6214`
- selected v2 no-token-frequency mean PPL: `14.2653`
- HDQS++ v3 mean PPL: `13.2341`

The interpretation follows the generated method status report and does not claim supported improvement unless the status and seed budget allow it.

3B adds OpenWebText and C4 English real HuggingFace streaming samples. These are explicitly bounded streaming samples, not complete upstream corpora. Their evidence is reported in `artifacts/cross_dataset/` and `docs/CROSS_DATASET_AUDIT.md`.

Future publication and reviewer notes are archived under `docs/future_publication_notes/`. They are future publication gap notes, not current release claims.

## Boundary

`method_debug` and filtering-only artifacts remain isolated from `main_results`. V3 ablation rows are model-training diagnostics, not primary method claims.
