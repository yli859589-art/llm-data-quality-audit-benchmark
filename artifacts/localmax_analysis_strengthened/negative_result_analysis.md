# LocalMax Strengthened Negative Result Analysis

This report is based on strengthened LocalMax artifacts only.
It does not make a full-scale mechanism conclusion, Level 3 claim, CCF-B-ready claim, or broad URD-win claim.

## Statistical Guardrails

- Comparisons use `valid_loss`; clipped PPL is reference-only.
- Improvement is disallowed when the confidence interval crosses zero.
- If URD fixed does not beat raw under the guarded comparison, that negative result is retained.
