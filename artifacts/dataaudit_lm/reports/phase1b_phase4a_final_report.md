# Phase 1B-Phase 4A Final Report

Status: `completed_with_release_gate_not_ready`

Branch: `codex/dataaudit-lm-refactor`

Start commit: `cdab17f095e35496ebbad7b10a96cb8d2d2d81ff`

Readiness label: `NOT_READY_FOR_FINAL_MATRIX`

This round completed the DataAudit-LM migration rehearsal and release-gate semantics cleanup. It did not run the final multi-seed matrix, did not claim final release readiness, and did not rename legacy results as new fair results.

## What Changed

- Added real DataAudit-LM data ingestion, record, sampling, split, sharding, and manifest utilities.
- Added mainline filters for raw retention, exact dedup, minhash near-dedup, length filtering, random token-matched filtering, quality rules, frozen reference-LM scoring, and selector scaffolding.
- Added decoder-LM training utilities for cold-start initialization, corpus-wide sampling, checkpoints, lineage, and smoke rehearsal training.
- Added evaluation/statistics utilities for token-weighted NLL, target-only downstream masking, bootstrap, paired tests, multiple-testing correction, and effect sizes.
- Added backup restore verification, migration map, naming inventory, protocol freeze manifest, and rehearsal reports.
- Split release finalization into `--audit-only` and `--release` modes so an unmet final gate cannot be mistaken for a successful release.
- Updated `run_all_checks.py` so stable default checks pass while heavy execution groups are explicit opt-in and recorded as skipped.
- Restored CI coverage for full pytest, ruff, black, mypy, repo hygiene, DataAudit checks, rehearsal, and release-gate behavior.

## Release Gate

`final_release_gate_passed` remains `false`.

- `python scripts/dataaudit_lm/finalize_release.py --audit-only` exits 0 and reports `AUDIT_COMPLETED_RELEASE_NOT_READY`.
- `python scripts/dataaudit_lm/finalize_release.py --release` exits 1 and reports `RELEASE_GATE_FAILED`.

Interpretation: audit completion is not final release approval.

## Validation

- `python -m pytest -q`: `307 passed in 178.66s`
- `python scripts/run_all_checks.py --timeout 300`: passed
- `ruff check .`: passed
- `black --check .`: passed
- active-scope Black check for DataAudit-LM files: passed
- `mypy src/dataaudit_lm`: passed for 43 source files
- `python scripts/check_repo.py --clean`: passed
- `python scripts/dataaudit_lm/verify_backup_restore.py`: passed
- `python scripts/dataaudit_lm/generate_naming_inventory.py`: new mainline scope hit count 0

Default skipped heavy groups in `run_all_checks.py`:

- `level3_execution_checks`
- `localmax_execution_checks`
- `localmax_v2_execution_checks`
- `localmax_v2_release_checks`
- `localmax_ccfc_artifact_checks`

These groups remain available through the explicit heavy-check path; they are not counted as completed final matrix evidence.

## Protected Files

Protected result hashes remained unchanged:

- `artifacts/tables/main_results.csv`: `EAB3478D19E04CAF97E07FC31FCD3CC36089C19320A64E96F7BAC9EB12D89921`
- `artifacts/stats/main_results.csv`: `E40944BB6476D84E8C3FC65670B2DC5E7DB62CF47CA7FC6D0051768458CD0E32`
- `artifacts/cross_dataset/cross_dataset_results.csv`: `8DA3E015146193FCD5D1F5F47A9E0A5ED84F55A4182B4BB5932DC657B8DAAD4C`
- `artifacts/runs/run_registry.jsonl`: `A05A06FCA305CEDF2C46DBEAD17AC222A5F09E73AB105538479A049DF90A26CE`

## Backup Restore

Backup restore was verified.

- Restored head: `16b33e8e6fc97be1c0f3475abb23ea8ced9571c8`
- Temporary restore directory cleaned: true

## Naming Migration

- New mainline scope hit count: 0
- Full repository legacy hit count: 2399

The new DataAudit-LM mainline scope is clean. Legacy artifacts and documentation remain preserved and classified instead of being deleted.

## Rehearsal Boundary

The rehearsal completed and produced finite NLL values with cold-start training lineage. Its comparison scope is `NOT_FOR_METHOD_COMPARISON`; it verifies wiring, lineage, and fairness checks only.

## Remaining Blockers

- Remote GitHub Actions still needs to be observed after pushing this branch.
- Full final matrix has not been executed under the frozen protocol.
- Tokenizer path is not yet fully migrated into the new DataAudit-LM mainline.
- Registry still contains adapter-only legacy evidence and must be replaced by new mainline artifacts in later phases.
- Final release gate remains false by design.

Recommended next step: push the branch, inspect remote CI, then continue with tokenizer/mainline registry migration before any final multi-seed matrix.
