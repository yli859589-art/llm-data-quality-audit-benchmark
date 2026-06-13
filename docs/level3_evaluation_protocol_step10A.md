# Level 3 Evaluation Protocol Step 10A

The evaluation protocol defines future evidence across language-model metrics,
downstream benchmarks, risk, diversity, cost, stability, and Pareto analysis.

## Required Evaluation Types

- Validation loss and perplexity under fixed token budgets.
- Token-normalized and budget-normalized utility.
- Risk metrics.
- Diversity metrics.
- Cost metrics.
- Stability and statistical uncertainty.
- Pareto tradeoff summaries.
- Downstream benchmarks.

## Downstream Minimum

At least three downstream benchmarks are required. The Step 10A protocol names
`LAMBADA`, `PIQA`, `HellaSwag`, `ARC-Easy`, and optional `BoolQ` or
`Winogrande`.

## Boundary

Step 10A downstream entries are protocol-only. They are not completed downstream
evidence and cannot be used as method-success claims.

