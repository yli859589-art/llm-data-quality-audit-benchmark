# LLM Data Quality Audit Benchmark

Current status: `TOP_TIER_CCFC_PROJECT_CANDIDATE`

LocalMax V2 status: `LOCAL_MAX_V2_STRONG_EVIDENCE_RELEASED`

Level 3 status: `not completed`

Bundle scope: `standalone_metadata_bundle`

This repository is a reproducible research artifact for auditing language-model pretraining data filters under controlled token budgets.

The project does **not** claim a completed Level 3 benchmark, publication-tier readiness, institutional affiliation, competition placement, official downstream completion, or a supported method win over raw training data.

The original LocalMax V1 release remains available as the minimal training evidence baseline. V1 uses valid_loss as the comparison metric; its PPL values are clipped and not comparable.

## CCF-C Candidate Evidence

The current strongest evidence line is `LocalMax CCFC`, an expanded local research artifact built on the LocalMax V2 data pipeline rather than a separate rewritten project.

- Data: 2 real non-fallback datasets, `200006900` GPT-2 tokens total.
- Methods: raw, exact_dedup, length_filter, random_same_keep_rate, c4_quality_filter, perplexity_proxy_filter, urd_fixed.
- Training: 42 small-model runs across 2 datasets x 7 methods x 3 seeds.
- Budget: each completed run sees `5001216` training tokens; total CCF-C candidate training tokens_seen is `210051072`.
- Model: small decoder LM, about 20.5M parameters, GPT-2 tokenizer, context length 256.
- Evaluation: per-seed language-model metrics, risk/diversity/cost tables, bootstrap-style summaries, dataset-level method rankings, and a local cloze-style downstream probe.
- Safe interpretation: the evidence is strong enough to describe as a top-tier CCF-C prototype candidate, but it is not an accepted paper, not an official competition result, and not a completed Level 3 / CCF-B artifact.

See `docs/LOCALMAX_CCFC_PROJECT_REPORT.md`, `docs/LOCALMAX_CCFC_CLAIM_BOUNDARY.md`, and `artifacts/localmax_ccfc_tables/`.

## LocalMax V2 Summary

- Data: 2 real non-fallback datasets, `200006900` GPT-2 tokens total.
- Methods: raw, exact_dedup, length_filter, urd_fixed.
- Training: 24 small-model runs, each >=1M tokens_seen.
- Model: small decoder LM, about 20.5M parameters, GPT-2 tokenizer, context length 256.
- Main comparison metric: `valid_nll_nats_per_token`.
- PPL is computed without clipping; no PPL-improvement claim is made unless supported by the tables.
- Level 3 remains unfinished.
- CCF-B readiness is not claimed.
- The release bundle excludes raw data and large binary checkpoints.

## Quick Start

```bash
python scripts/localmax_v2/finalize_localmax_v2_release.py
python scripts/localmax_v2/audit_lm_metric_correctness.py
python scripts/localmax_ccfc/check_ccfc_artifacts.py
python -m pytest tests/ -q
```

For the full grouped validation wrapper:

```bash
python scripts/run_all_checks.py --timeout 600
```

## Reproducibility Notes

The release directory contains metadata, metrics, tables, figures, reports, and copied manifests needed for review. It does not contain raw data text or full binary checkpoints.

Historical single-seed and smoke artifacts are retained for lineage, but they are not the LocalMax V2 main evidence.

URD-Selector is implemented as a smoke-verified selector pipeline, but it is not yet effectiveness-verified or current main evidence.

## Usage Note

This can be discussed as a personal research and portfolio prototype only if the wording keeps the evidence boundary above. Do not present it as official coursework, a competition result, or a completed publication-level benchmark.

See `docs/LOCALMAX_V2_RESULTS.md` and `artifacts/localmax_v2_release/`.
