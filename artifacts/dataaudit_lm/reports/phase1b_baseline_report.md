# Phase 1B Baseline Report

- Branch: `codex/dataaudit-lm-refactor`
- Start commit: `cdab17f095e35496ebbad7b10a96cb8d2d2d81ff`
- Status: `completed_with_failures_recorded`

## Baseline Command Results

- `git_status_short`: `dirty` - dirty worktree with root docs and LocalMax generated artifacts modified before this round
- `python_m_pytest_q_initial`: `failed` - 4 failed, 286 passed in 165.89s
- `python_m_pytest_q_x`: `failed` - 1 failed, 138 passed in 71.47s
- `python_m_pytest_q_tb_long_after_state_refresh`: `passed` - 290 passed in 154.35s
- `ruff_check_initial`: `failed` - 1551 legacy lint findings before transitional config cleanup
- `black_check_initial`: `blocked` - Black 25.1.0 refused to run on local Python 3.12.5 safety guard
- `mypy_src_dataaudit_lm_initial`: `passed` - Success: no issues found in 13 source files

## Initial Failed Tests

- `tests/test_localmax_readme_resume_step10C.py::test_readme_reports_localmax_release_without_overclaiming`: README role conflict: LocalMax legacy status was expected in root README while DataAudit-LM needs the root README identity. Fix: move LocalMax assertions to docs/LOCALMAX_RELEASE.md and keep README as DataAudit-LM.
- `tests/test_localmax_release_bundle_scope_step10C_hotfix.py::test_docs_and_readme_disclose_bundle_scope`: same README role conflict; bundle scope belongs to LocalMax release docs, not DataAudit-LM README. Fix: check docs/LOCALMAX_RELEASE.md and docs/LOCALMAX_REPRODUCIBILITY.md.
- `tests/test_localmax_release_cross_platform_hashes_step10C_hotfix.py::test_generated_text_artifacts_use_lf_newlines`: generated claim-check artifacts were stale and/or rewritten with different canonical bytes. Fix: rerun canonical LocalMax claim checker and keep generated output stable.
- `tests/test_localmax_release_idempotency_step10C_hotfix.py::test_claim_checker_repeated_run_is_idempotent`: first checker run changed tracked report from failed/stale to ok, so before/middle hash differed. Fix: remove README dependency from LocalMax claim checker and commit stable claim-check outputs.

## Baseline Blockers

- final release gate false but finalize_release.py exited success without mode distinction
- raw ingestion / exact dedup behavior not implemented in new package
- cluster-aware split not implemented in new package
- reference-LM scoring not implemented in new package
- training initialization and corpus-wide sampling not implemented in new package
- token-weighted NLL and target-only downstream scoring not implemented in new package
- backup bundle existed but had not been restore-verified in this round
- run_all_checks default included heavy execution groups unsuitable for CI default
