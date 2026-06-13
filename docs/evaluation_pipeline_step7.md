# Step 7 Evaluation Pipeline

Step 7 adds `evaluation_v2`, a unified evaluation infrastructure layer for the
Level 3 upgrade path. It expands the project beyond a single loss/PPL-centered
view, but it does not add new main results.

No model training was run in Step 7. No official downstream benchmark was run.
No PPL or downstream result was added to the canonical main tables. No
effectiveness claim is allowed from Step 7 alone.

## Why PPL Is Not Enough

Validation loss and PPL are useful, but data filtering can fail in ways that a
single utility metric hides. A filter can lower risk while losing diversity, or
retain diverse text while increasing cost. Step 7 therefore defines a multi-view
evaluation contract before later heavier experiments are run.

## Architecture

The new code lives under `src/evaluation_v2/`:

- `base.py`: `EvaluationConfig`, `EvaluationInput`, `EvaluationResult`, and
  `BaseEvaluator`.
- `schema.py`: Step 7 manifest constants and scope boundaries.
- `manifest.py`: evaluation manifest writer and artifact hashing.
- `io.py`: JSON, JSONL, CSV, and path helpers.
- `lm_metrics.py`: Step 5 smoke LM metrics wrapper.
- `downstream.py`: downstream benchmark protocol matrix.
- `risk_eval.py`: risk proxy evaluator.
- `diversity_eval.py`: diversity proxy evaluator.
- `cost_eval.py`: cost proxy evaluator.
- `stability.py`: stability interface with insufficient-evidence warnings.
- `pareto.py`: Step 6 Pareto artifact reader and diagnostic summarizer.
- `statistics.py`: mean/std/SE/bootstrap/rank-correlation helpers with
  insufficient-sample warnings.
- `validation.py`: evaluation manifest and no-main-results-pollution checks.
- `reporting.py`: small Markdown report helper.

The script entry points are:

- `scripts/evaluate_all_v2.py`
- `scripts/check_evaluation_manifests.py`

## Manifest Schema

Every Step 7 output writes `evaluation_manifest.json` with:

- manifest version: `step7.evaluation_manifest.v1`;
- evaluation type and scope;
- smoke/protocol/completion flags;
- input, training, filter, tokenizer, metrics, and report paths;
- real SHA-256 hashes for present artifacts;
- `no_main_results_written: true`;
- `effectiveness_claim_allowed: false`.

Smoke evaluations must set `smoke_only=true`. Protocol outputs must set
`protocol_only=true`. Protocol-only downstream outputs must not claim
completion.

## Evaluation Families

LM metrics:
Reads the Step 5 smoke training manifest and metrics file, then writes
`lm_metrics.json`. The validation PPL in this file is a smoke diagnostic only.

Downstream protocol:
Records the planned LAMBADA, PIQA, HellaSwag, ARC-Easy, BoolQ, Winogrande, and
tiny local smoke task interfaces. No external benchmark is downloaded.

Risk:
Reads Step 6 URD smoke artifacts and writes risk proxy metrics. Toxicity
classification is marked unavailable.

Diversity:
Reads Step 6 URD smoke artifacts and writes lexical/hash diversity diagnostics.
Neural embedding diversity is marked unavailable.

Cost:
Reads Step 6 cost reports and optionally Step 5 training manifests. Real FLOPs
are not measured. Training-cost fields remain unavailable unless an explicit
training manifest is supplied.

Stability/statistics:
Provides safe utilities for mean, standard deviation, standard error, bootstrap
CI, paired difference, and rank correlation. Insufficient sample sizes return
warnings instead of unsupported significance claims.

Pareto:
Reads Step 6 Pareto artifacts and produces diagnostic tables. It does not claim
that any frontier is better.

## What Step 7 Actually Ran

Step 7 generated smoke/protocol outputs under `artifacts/evaluation_step7/`:

- `wikitext2_smoke/lm_bpe_tiny/`
- `wikitext2_smoke/risk_urd_fixed/`
- `wikitext2_smoke/diversity_urd_fixed/`
- `wikitext2_smoke/cost_urd_fixed/`
- `wikitext2_smoke/pareto_urd_pareto/`
- `downstream_protocol/`
- `stability_protocol/`

Each directory includes an `evaluation_manifest.json`. Smoke directories also
include their metrics and Markdown report. The downstream directory contains a
protocol matrix only. The stability directory is protocol-only and records
insufficient evidence for rank stability.

`configs/evaluation/combined_smoke.yaml` is retained as a config-only smoke
matrix descriptor. It is not a runnable combined evaluator and is not completed
evidence.

## What Step 7 Did Not Run

Step 7 did not:

- train a model;
- run official downstream benchmarks;
- run downstream tiny local tasks as completed evidence;
- add a canonical PPL result;
- add a canonical downstream result;
- add a main table row;
- evaluate URD as an effective method;
- perform mechanism analysis.

## Claim Boundary

Safe claims:

- Step 7 implements evaluation infrastructure.
- LM/risk/diversity/cost/Pareto smoke evaluators run offline on CPU.
- Downstream benchmark protocol output exists.
- Evaluation manifests and hashes are machine-checkable.

Unsafe claims:

- Step 7 proves method effectiveness.
- Step 7 proves downstream improvement.
- Step 7 establishes a better Pareto frontier.
- Step 7 does not complete the Level 3 heavy evidence package.

## Next Steps

Step 8 should analyze mechanisms and failure modes using the evaluation
interfaces created here. Step 10 is the appropriate place for a frozen heavy
evaluation release after real registered experiments exist.
