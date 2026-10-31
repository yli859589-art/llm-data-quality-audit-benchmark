# Final project acceptance — P2-2

## Acceptance dimensions

| Dimension | Status | Evidence |
| --- | --- | --- |
| Software system | PASS (bounded scope) | Unified CLI/service/UI, isolated outputs, task persistence, export, regression tests, packaging verification. |
| Formal real-data/model experiments | BLOCKED_BY_MISSING_DATA | All nine declared C4/OpenWebText source shards are absent; no 200M-token run is claimed. |

## Verified P2-2 facts

- The P2-1 service calls the P1-2 pipeline for Raw runs and existing `filters_v2`
  implementations for the remaining strategies.  Global/batch algorithms retain
  their explicit `max_documents` bound; only Raw is claimed as a fully streaming
  system operation.
- Full-state CPU checkpoint interruption/resume is compared against an
  uninterrupted two-step run in `tests/test_p2_final_acceptance.py`.
- The downstream-protocol legacy manifest has mismatching metrics and report
  hashes.  The tracked files have no post-baseline commit history, so P2-2
  preserves them and generates a read-only audit rather than rewriting evidence.
- The persistent LSH index no longer hashes every incoming document twice.
  Candidate retrieval and exact Jaccard confirmation are unchanged.

Machine-readable P2-2 reports are emitted only under
`artifacts/upgrade_reports/p2-02/` and are intentionally not release evidence
until their listed commands have actually completed.
