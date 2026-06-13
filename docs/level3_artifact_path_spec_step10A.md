# Level 3 Artifact Path Specification Step 10A

Step 10A freezes future Level 3 artifact locations so later execution does not
mix heavy evidence with historical, smoke, or protocol-only outputs.

## Artifact Roots

- Data: `artifacts/level3_data/`
- Tokenizers: `artifacts/level3_tokenizers/`
- Filters: `artifacts/level3_filters/`
- Training: `artifacts/level3_training/`
- Evaluation: `artifacts/level3_evaluation/`
- Analysis: `artifacts/level3_analysis/`
- Tables: `artifacts/level3_tables/`
- Figures: `artifacts/level3_figures/`
- Reports: `artifacts/level3_reports/`
- Release: `artifacts/level3_release/`

## Named Outputs

- `artifacts/level3_tables/main_results_level3.csv`
- `artifacts/level3_reports/baseline_matrix_report.md`
- `artifacts/level3_reports/urd_selector_report.md`
- `artifacts/level3_reports/downstream_report.md`
- `artifacts/level3_reports/mechanism_report.md`
- `artifacts/level3_release/level3_release_candidate.zip`

These paths are future destinations. They are not evidence of completed heavy
execution in Step 10A.

## Step 10A-Hotfix Reproducibility Rules

Artifact step detection uses repo-relative POSIX paths before matching step
tokens. Parent directory names such as `step10a_audit` or `step1_review` must
not affect whether an artifact is classified as Step 4, Step 7, Step 8, or
Step 10A.

The artifact registry must be finalized after generated reports are written.
If a report is rewritten after registry generation, the registry hash check must
fail until the registry is regenerated. A registry hash mismatch is a
reproducibility failure, not a warning to ignore.

Step 10A still does not execute heavy jobs. Step 10B remains the first stage
allowed to prepare heavy data or run heavy training.
