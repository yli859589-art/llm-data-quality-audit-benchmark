# LLM Data Quality Diagnostics and Risk Auditing Benchmark

## Problem

Data-quality filters are often assumed to improve LLM pretraining data, but
proxy quality scores can fail under real training evaluation.

## Approach

Build a reproducible audit benchmark that compares raw data, random same
keep-rate, dedup, and HDQS++ variants under shared tokenizer/model/evaluation
controls.

## System Components

- Real data manifests and split-integrity checks
- Small-model training loop
- Multi-seed baselines
- Append-only run registry
- Artifact lineage checks
- Claim hygiene and fresh-unzip release verification
- Cross-dataset streaming-sample audit

## Main Findings

- Raw is currently the strongest WikiText-2 mean-PPL baseline.
- HDQS++ v3 improves over v2 trend-wise but does not outperform raw.
- OpenWebText/C4 evidence is based on real streaming samples, not complete
  upstream dataset runs.

HDQS++ v3 does not outperform raw under the current fair benchmark.

## Reproducibility Mechanisms

- `python scripts/run_all_checks.py --timeout 300`
- `python scripts/run_release_checks.py --timeout 300`
- `python scripts/check_claim_hygiene.py`
- `python scripts/verify_fresh_unzip.py --zip <release.zip> --timeout 300`

## Why It Matters

The project shows how to audit data filtering risk instead of assuming that a
filter is useful because its proxy score looks better.

## Current Limitations

- `small` model only
- 3 seeds only
- streaming-sample cross-dataset evidence
- no supported method improvement over raw

## Next Steps

4A can add a BPE tokenizer, medium model, larger streaming samples, stronger
baselines, held-out test evaluation, mechanism diagnostics, and compute logs.
