# Step 6 URD-Selector

Step 6 implements the URD-Selector pipeline:

`Utility-Risk-Diversity Selection for Language Model Pretraining Data`.

This step is implementation and smoke verification only. No model training was
run in Step 6. No PPL result, downstream result, or main experiment row was
added. URD smoke selections are not main evidence, and URD effectiveness must be
evaluated in later steps.

## Why Not HDQS++ v4

HDQS++ remains preserved as a historical baseline and failure-analysis object.
Continuing to rename or tune HDQS++ would make the project look deeper without
creating a clearer research contract. URD-Selector is a separate planned main
method direction with independent components, independent manifests,
independent ablations, and two selection modes.

## HDQS++ Versus URD-Selector

HDQS++ is a historical heuristic quality filter. It is useful because its
negative evidence shows that plausible quality filters can fail under fair
small-model controls.

URD-Selector is a selector pipeline. It explicitly decomposes the selection
decision into utility, risk, diversity, shift, and cost signals. In Step 6 those
signals are lightweight proxies. They are not yet validated as a superior
method and should not be reported as model-quality evidence.

## Components

URD uses five component families:

- Utility: length-normalized lexical informativeness, rare-token coverage,
  entropy, and validation-similarity proxies.
- Risk: URL, HTML/noise, symbol, repetition, digit, PII-pattern, boilerplate,
  and duplicate-hint proxies.
- Diversity: lexical diversity, unique-token ratio, entropy, source coverage,
  hash-vector novelty, and cluster-coverage proxies.
- Shift: input-relative length, vocabulary, and source-distribution shift
  penalties.
- Cost: document length, estimated token, runtime, dependency, and CPU/memory
  proxies.

All component scores are normalized to `[0, 1]`. Risk, shift, and cost are
penalties where higher means more risk or cost. Utility and diversity are
positive objectives where higher means more desirable under the proxy.

## Fixed-Weight Mode

`urd_fixed` computes:

```text
score = alpha * utility
      + beta * diversity
      - gamma * risk
      - lambda_shift * shift_penalty
      - mu_cost * cost
```

The default weights are declared in `configs/filters/urd_fixed.yaml` and copied
into the filter manifest. They are transparent defaults for smoke selection, not
post-hoc evidence-tuned weights.

## Pareto Mode

`urd_pareto` computes component scores, then performs transparent
non-dominated sorting over:

- maximize utility;
- maximize diversity;
- minimize risk;
- minimize shift penalty;
- minimize cost.

It writes `pareto_frontier.csv` and `pareto_layers.json`. This is a
Pareto-style smoke implementation, not a full multi-objective evaluation.
Step 7 should evaluate metrics; Step 8 should analyze mechanisms.

## Ablation Design

The Step 6 ablation configs are:

- `configs/filters/urd_ablation_no_utility.yaml`
- `configs/filters/urd_ablation_no_risk.yaml`
- `configs/filters/urd_ablation_no_diversity.yaml`
- `configs/filters/urd_ablation_no_shift.yaml`
- `configs/filters/urd_ablation_no_cost.yaml`

Each ablation disables one component for smoke selection. These configs do not
prove a component helps. They only make the future ablation surface explicit.

## Proxy Policy

All Step 6 components are lightweight proxies. Optional safety classifier,
neural embedding diversity, proxy LM, FLOPs, and full mechanism-analysis signals
are marked unavailable when not implemented. Step 6 does not use external model
downloads or hidden evaluators.

## What Step 6 Actually Ran

Step 6 generated smoke filter outputs on Step 2 WikiText-2 smoke data:

- `artifacts/filter_outputs_step6/wikitext2_smoke/urd_fixed/`
- `artifacts/filter_outputs_step6/wikitext2_smoke/urd_pareto/`
- `artifacts/filter_outputs_step6/wikitext2_smoke/urd_ablation_no_risk/`

Each output directory contains:

- `filter_manifest.json`
- `component_scores.jsonl`
- `selected_doc_ids.jsonl`
- `decisions.jsonl`
- `scores.jsonl`
- `keep_rate_report.json`
- `risk_report.json`
- `diversity_report.json`
- `cost_report.json`
- `urd_summary.json`

The Pareto run also contains:

- `pareto_frontier.csv`
- `pareto_layers.json`

## What Step 6 Did Not Run

Step 6 did not run model training, independent downstream evaluation, formal
rank stability, bootstrap confidence intervals, full Pareto evaluation, or
mechanism analysis. It did not write any URD row into `main_results`.

## Claim Boundary

Safe claims:

- URD-Selector pipeline code exists.
- Fixed-weight and Pareto smoke selections run offline on CPU.
- Component scores, summaries, manifests, and smoke outputs are available.
- URD is a planned Level 3 main-method candidate.

Unsafe claims:

- URD has established model-quality effectiveness.
- URD smoke selections are main evidence.
- Step 6 proves a PPL or downstream improvement.
- Step 6 does not complete Level 3.
- Step 6 changes `ccf_b_ready` or `level3_pipeline_ready`.

## Next Steps

Step 7 should add evaluation metrics and compare URD against raw, random,
dedup, length, historical HDQS++, and stronger baselines under matched budgets.
Step 8 should analyze why URD succeeds or fails through mechanism and
failure-case analysis.
