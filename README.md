# LLM Data Quality Diagnostics and Risk Auditing Benchmark

## Project Overview

This repository is a personal research and portfolio prototype for auditing LLM
data-quality filtering risk. It provides a reproducible benchmark around real
data, fair baselines, artifact lineage, failure diagnostics, and claim-safety
checks.

It does **not** claim institutional affiliation, official coursework completion,
private-grader access, publication acceptance, competition placement, or
supported improvement over raw training data.

Canonical reporting language is maintained in
`docs/REPORTING_CONTRACT.md`.

## How To Review This Release

- 30 seconds: read `PROJECT_ONE_PAGE.md`.
- 3 minutes: read `PROJECT_SUMMARY.md` and `docs/FIGURE_INDEX.md`.
- 10 minutes: read `TECHNICAL_OVERVIEW.md`, `DEMO_GUIDE.md`, and
  `docs/CROSS_DATASET_AUDIT.md`.
- 1 hour: run the reproducibility commands, inspect
  `artifacts/release/final_release_report.md`, and verify the fresh-unzip
  report.

## Why Data Quality Filtering Needs Auditing

Data-quality filters can look useful before training: they remove noisy pages,
reduce repetition, preserve distribution shape, and keep high-scoring text. Under
a fair tokenizer, model, and validation budget, however, the filtered corpus can
still underperform raw data, seeded random retention, or exact deduplication.

The project value is therefore not a positive method-success claim. The value is
a reproducible audit framework that can detect when heuristic filtering is
fragile, overfilters, or shifts the training distribution.

## Key Findings

- The raw baseline is currently the strongest mean-PPL method on the WikiText-2
  dev benchmark.
- HDQS++ v3 improves over HDQS++ v2 trend-wise, but it does not outperform raw
  under the current fair benchmark.
- Raw, `random_same_keep_rate`, and `dedup_only` remain strong baselines in the
  completed setting.
- OpenWebText and C4 English evidence is based on real HuggingFace streaming
  samples, not complete upstream dataset runs.
- single-seed and diagnostic ablation signals are treated as diagnostic only,
  never as stable method conclusions.

## Quick Start

Install dependencies:

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
python -m pip install -e .
```

Run the local check suite:

```bash
python scripts/run_all_checks.py --timeout 300
```

Run claim hygiene directly:

```bash
python scripts/check_claim_hygiene.py
```

Regenerate dashboards:

```bash
python scripts/generate_project_dashboard.py
```

Run release checks:

```bash
python scripts/run_release_checks.py --timeout 300
```

Verify a release zip from a clean extraction:

```bash
python scripts/verify_fresh_unzip.py --zip path/to/release.zip --timeout 300 --skip-heavy
```

When GNU Make is available:

```bash
make check
make release-check
```

On Windows systems that provide MinGW Make as `mingw32-make`:

```bash
mingw32-make check
mingw32-make release-check
```

## Benchmark Protocol

Primary WikiText-2 candidate evidence:

- dataset: `wikitext2_paper`
- dataset_status: `real_local_nonfallback`
- dataset_scope: `official_split`
- model size: `small`
- seeds: `1 2 3`
- train_tokens: `1228800`
- evaluated_validation_tokens: `53248`

Cross-dataset audit evidence:

- `openwebtext_streaming`: `real_nonfallback`, `streaming_sample`
- `c4_en_streaming`: `real_nonfallback`, `streaming_sample`

Streaming-sample rows are audit evidence. They are not paper-scale claims and
must not be described as complete upstream OpenWebText/C4 results.

## Results Snapshot

Lower mean PPL is better.

| Dataset | Scope | Method | Mean PPL | Safe interpretation |
|---|---|---|---:|---|
| `wikitext2_paper` | `official_split` | `raw` | 12.6214 | strongest current WikiText-2 mean baseline |
| `wikitext2_paper` | `official_split` | `random_same_keep_rate` | 12.7058 | close baseline |
| `wikitext2_paper` | `official_split` | `dedup_only` | 12.7261 | close baseline |
| `wikitext2_paper` | `official_split` | `hdqspp_v3` | 13.2341 | improves over v2 trend-wise, not raw |
| `openwebtext_streaming` | `streaming_sample` | `raw` | 133.5411 | strongest current streaming-sample mean baseline |
| `openwebtext_streaming` | `streaming_sample` | `hdqspp_v3` | 253.3836 | does not outperform raw on this streaming sample |
| `c4_en_streaming` | `streaming_sample` | `raw` | 174.5871 | tied with dedup as strongest current streaming-sample mean baseline |
| `c4_en_streaming` | `streaming_sample` | `hdqspp_v3` | 302.9781 | does not outperform raw on this streaming sample |

The complete canonical result boundary is in `docs/REPORTING_CONTRACT.md`.

## Cross-Dataset Audit

3B extends the audit from WikiText-2 to OpenWebText and C4 English real
streaming samples. The cross-dataset artifacts separate completed, failed,
configured-only, and lightweight rows:

- `artifacts/cross_dataset/cross_dataset_results.csv`
- `artifacts/cross_dataset/dataset_status_matrix.csv`
- `artifacts/cross_dataset/cross_dataset_summary.md`
- `docs/CROSS_DATASET_AUDIT.md`

The cross-dataset result is a risk-audit expansion, not a supported over-raw
method claim.

## Reproducibility

Important verification commands:

```bash
python scripts/check_repo.py --clean
python -m pytest -q
python scripts/check_claim_hygiene.py
python scripts/run_all_checks.py --timeout 300
python scripts/run_release_checks.py --timeout 300
python scripts/check_experiment_readiness.py
```

Rebuild the main WikiText-2 tables:

```bash
python scripts/analyze_significance.py --input artifacts/runs/run_registry.csv --output artifacts/stats
python scripts/generate_tables.py
python scripts/check_main_results_purity.py
```

Rebuild the cross-dataset audit:

```bash
python scripts/generate_cross_dataset_tables.py
python scripts/analyze_cross_dataset_audit.py
```

## Artifact Lineage

The append-oriented registry records training, filtering, data-preparation,
failed, and superseded rows:

- `artifacts/runs/run_registry.jsonl`
- `artifacts/runs/run_registry.csv`
- `artifacts/runs/migration_log.jsonl`

Failed or superseded runs are retained for audit integrity rather than removed
to make the project look cleaner.

## Claim Boundary

This release is a reproducible audit benchmark. It does not claim that HDQS++ v3
outperforms raw data under the current fair benchmark.

This is an experiment-candidate benchmark release, not a CCF-C-ready paper
artifact.

Do not claim:

- supported HDQS++ improvement over raw
- method-leadership or publication-ready method status
- complete upstream OpenWebText/C4 benchmark completion
- statistically supported improvement over raw
- large-scale or web-scale corpus results

## Limitations

- Current model scale is `small`.
- The main protocol uses 3 seeds, so claims remain preliminary.
- OpenWebText/C4 evidence is streaming-sample evidence only.
- The tokenizer/model setting is limited.
- Held-out test evaluation should only be used after method settings are frozen.
- HDQS++ v1/v2/v3 do not have supported improvement over raw in current evidence.

## Roadmap

- 3C-1: freeze reporting contract and claim boundary.
- 3C-2: clean public release structure and packaging.
- 3C-3: prepare optional one-page summary, demo guide, and resume bullets under
  the same reporting contract.
- Future: run larger samples, larger model scales, and stronger seed budgets
  before revisiting any method-success claim.

## Documentation

Start here:

- `PROJECT_ONE_PAGE.md`
- `PROJECT_SUMMARY.md`
- `TECHNICAL_OVERVIEW.md`
- `DEMO_GUIDE.md`
- `RESUME_BULLETS.md`
- `docs/REPORTING_CONTRACT.md`
- `docs/QUICKSTART.md`
- `docs/BENCHMARK_PROTOCOL.md`
- `docs/REPRODUCIBILITY.md`
- `docs/ARTIFACT_INDEX.md`
- `docs/PROJECT_EVIDENCE_MAP.md`
- `docs/CROSS_DATASET_AUDIT.md`
- `docs/FIGURE_INDEX.md`
- `docs/LIMITATIONS.md`
- `docs/METHOD_DASHBOARD.md`
- `RELEASE_NOTES.md`
- `artifacts/release/final_release_report.md`
