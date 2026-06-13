# Level 3 Technical Debt

## Fixed in Step 9

- Added Level 3 readiness states and gates.
- Added artifact registry v2.
- Added Level 3 claim map.
- Added no-smoke, no-protocol, and no-Level2-as-Level3 checks.
- Added registry-to-table consistency checks.
- Hardened `run_all_checks.py` with groups and JSON/Markdown reports.
- Marked Step 5 resume and independent eval split support truthfully as not
  supported.
- Added run metadata to the Step 5 training registry.
- Added a Step 6 URD manifest extension marker.
- Added a Step 7 stability protocol artifact.
- Added single-file support to `check_mechanism_manifests.py --path`.

## Fixed in Step 10A-Hotfix

- Artifact scanner step detection now uses repo-relative paths.
- Parent directory names containing `step1`, `step2`, or `step10a` no longer
  affect artifact step classification.
- `step10A_readiness_report.json` is classified as `step10A`, not `step1`.
- Artifact registry finalization now runs after report-generating checks.
- Registry hash mismatch remains a hard reproducibility failure.
- Step 10A readiness records the scanner and registry-order hardening fields
  without marking heavy execution complete.

## Remaining After Step 9

- Real 500M-token or larger BPE datasets are not prepared.
- Mainline GPT-2/BPE32k tokenizer matrix is not completed.
- Full strong baseline/filter matrix is not completed on heavy data.
- Medium and selected large-lite training are not completed.
- Official downstream benchmark execution is not completed.
- Full-scale mechanism analysis is not completed.
- Paper-ready figures remain a Step 10C requirement.

Step 10B remains the first heavy execution step. Step 10A-hotfix does not
prepare heavy data, train models, or add official downstream/PPL evidence.
