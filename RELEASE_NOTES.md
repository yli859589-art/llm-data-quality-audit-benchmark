# Release Notes

## Version

`3C-3-release-candidate-v1`

## Readiness

- readiness: `EXPERIMENT-CANDIDATE`
- benchmark_scope_status: `multi_dataset_audit_candidate`
- method_status: `honest_audit_framework`
- secondary_method_finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`
- ccf_c_ready: `false`

## Claim Boundary

This release is an LLM data-quality diagnostics and risk-auditing benchmark. It
does not claim that HDQS++ v3 outperforms raw under the current fair benchmark.
It is not a CCF-C-ready paper artifact.

## Main Result

The current WikiText-2 `small` model benchmark shows raw as the strongest mean
PPL baseline. HDQS++ v3 improves over HDQS++ v2 trend-wise as a secondary
diagnostic finding, but it does not support a method claim over raw.

## Cross-Dataset Status

3B cross-dataset audit evidence is present:

- `wikitext2_paper`: real local official split
- `openwebtext_streaming`: real HuggingFace streaming sample
- `c4_en_streaming`: real HuggingFace streaming sample

OpenWebText and C4 English are streaming-sample audits, not complete upstream
dataset runs.

## Release Structure Updates

- Added public display package files: `PROJECT_SUMMARY.md`,
  `PROJECT_ONE_PAGE.md`, `TECHNICAL_OVERVIEW.md`, `DEMO_GUIDE.md`,
  `RESUME_BULLETS.md`, `docs/PROJECT_PRESENTATION_NOTES.md`, and
  `docs/FIGURE_INDEX.md`.
- Added final release reporting under `artifacts/release/`.
- Fresh-unzip reports now distinguish `lightweight_check_status` from
  `heavy_check_status`; skipped heavy checks are reported as
  `skipped_by_request`, not as passed.
- Added `docs/README.md` as a documentation index.
- Archived paper, reviewer, submission, and CCF-C gap notes under
  `docs/future_publication_notes/`.
- Added `docs/FRESH_CLONE_TEST.md`.
- Added `scripts/verify_fresh_unzip.py`.
- Extended release checks to support zip and fresh-unzip verification.

## Known Limitations

- Current model scale is `small`.
- Current main protocol uses 3 seeds.
- Cross-dataset evidence is streaming-sample evidence.
- Method improvement over raw is unsupported.
- Held-out test evaluation should only be used after method settings are frozen.

## Route Forward

- 4A: future research only. Do not treat the roadmap as completed evidence in
  this release.
- Future: larger samples, larger models, stronger seed budgets, and clean CI release tags.
