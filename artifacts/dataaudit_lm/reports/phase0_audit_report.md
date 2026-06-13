# DataAudit-LM Phase 0 Audit Report

- Status: `completed_with_blockers`
- Baseline commit: `16b33e8e6fc97be1c0f3475abb23ea8ced9571c8`
- Backup branch: `backup/pre-dataaudit-refactor`
- Backup bundle: `C:\Users\18104\Desktop\backup_pre_dataaudit_refactor_20260613.bundle`
- Tracked files: `3066`
- Forbidden-term matches: `588`

## Baseline Test Results

- `python -m pytest -q`: failed, `285 passed, 2 failed`.
- `ruff check .`: failed, 1551 current-tree lint errors.
- `black --check .`: failed because this Python 3.12.5 build triggers Black AST safety warning.
- `mypy src/dataaudit_lm`: failed because `src/dataaudit_lm` does not exist yet.

## Current Evidence Snapshot

- completed_training_runs: `42`
- expected_training_runs: `42`
- filter_methods: `['c4_quality_filter', 'exact_dedup', 'length_filter', 'perplexity_proxy_filter', 'random_same_keep_rate', 'raw', 'urd_fixed']`
- target_tokens_seen_per_run: `5000000`
- min_tokens_seen_per_completed_run: `5001216`
- total_training_tokens_seen: `210051072`

## Blocking Findings

- Public repository currently contains rating/submission-oriented naming and content that the new prompt forbids.
- Current package layout is not src/dataaudit_lm.
- Current tests encode old LocalMax/Level naming and will be incompatible with the requested neutral public release.
- Current evidence is 2 datasets x 7 methods x 3 seeds = 42 runs, not the requested 2 x 8 x 5 = 80 run matrix.
- Current downstream evidence is local cloze probe only, not official cloze/PIQA/ARC-Easy.
- Current reference-LM filter is not yet verified as a true frozen reference-LM NLL filter under the requested spec.
- Current raw ingestion likely needs an audit for pre-dedup behavior before any exact-dedup claim is kept.

## Next Step

Create a clean DataAudit-LM refactor branch. Do not mark a final release until the missing gates are actually implemented and verified.
