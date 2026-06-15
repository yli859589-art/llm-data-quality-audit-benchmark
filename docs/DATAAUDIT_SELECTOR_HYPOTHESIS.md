# DataAudit Selector Hypothesis

Hypothesis: a useful pretraining-data selector must balance utility,
redundancy, risk, and domain coverage rather than optimizing a single surface
proxy.

The selector is evaluated against:

- `single_metric_reference_nll`
- `simple_linear_score`
- `pareto_selector`
- `dataaudit_selector`

The selector adds value only if it improves the utility-risk-cost tradeoff
under a frozen development protocol. It fails if it collapses to length
filtering, removes useful domain diversity, overfits final test data, or cannot
beat a token-matched random control.

Weights are frozen on a development subset before final evaluation. A null or
negative result is retained as research evidence, not hidden.
