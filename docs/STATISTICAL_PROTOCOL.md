# DataAudit-LM Statistical Protocol

Formal method comparison requires at least five seeds per dataset-method cell.
Single-seed rehearsal output is `ENGINEERING_VALIDATION_ONLY` and
`NOT_FOR_METHOD_COMPARISON`.

The frozen analysis plan is:

- paired seed differences against raw;
- mean and median effect summaries;
- bootstrap confidence intervals;
- paired t-test when assumptions are reasonable;
- Wilcoxon signed-rank as a non-parametric sensitivity check;
- effect size on paired differences;
- Holm correction across method families;
- win/tie/loss tables;
- negative and mixed results retained in reports.

No threshold or selector parameter may be tuned on final test results.
