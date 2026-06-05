# Demo Guide

## Five-Minute Read

1. Read `README.md` for project positioning.
2. Read `PROJECT_ONE_PAGE.md` for the short story.
3. Open `artifacts/tables/main_results.csv` and compare raw vs HDQS++ v3.
4. Open `docs/CROSS_DATASET_AUDIT.md` for streaming-sample evidence.
5. Open `artifacts/release/final_release_report.md` for release status.

## Quick Checks

```bash
python scripts/check_claim_hygiene.py
python scripts/check_experiment_readiness.py
python scripts/run_all_checks.py --timeout 300
```

## Main Results

Main WikiText-2 results are in:

- `artifacts/tables/main_results.csv`
- `artifacts/stats/main_results.csv`
- `docs/METHOD_DASHBOARD.md`

Safe interpretation: raw remains the strongest mean-PPL baseline in the current
main candidate matrix.

## Cross-Dataset Results

Cross-dataset audit rows are in:

- `artifacts/cross_dataset/cross_dataset_results.csv`
- `artifacts/cross_dataset/dataset_status_matrix.csv`
- `docs/CROSS_DATASET_AUDIT.md`

OpenWebText/C4 rows are real streaming samples, not full-dataset benchmarks.

## Explaining HDQS++ Failure

HDQS++ v3 does not outperform raw under the current fair benchmark. The demo
point is not "the method won"; the point is that a reproducible audit catches
when a plausible filter fails.

## Artifact Lineage

Show:

```bash
python scripts/check_artifact_lineage.py
```

Then open `artifacts/runs/run_registry.csv` and `docs/PROJECT_EVIDENCE_MAP.md`.

## Claim Hygiene

Show:

```bash
python scripts/check_claim_hygiene.py
```

Then open `artifacts/release/claim_hygiene_report.md`.

## honest_audit_framework

`honest_audit_framework` means the project value is real-data auditing,
baseline fairness, lineage, and failure diagnostics rather than a supported
method-success claim.

## Streaming Sample Boundary

OpenWebText and C4 evidence uses `dataset_scope=streaming_sample`. Do not call
these rows complete upstream OpenWebText/C4 results.
