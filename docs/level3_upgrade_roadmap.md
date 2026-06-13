# Level 3 Upgrade Roadmap

This roadmap upgrades the current experiment-candidate audit benchmark toward a
future DataAudit-LM / URD-Selector research artifact. It is a plan, not evidence
that Level 3 is complete.

## Step 0: Repository Audit and Asset Preservation

Goal: understand the current repository and lock its real state before
refactoring.

Allowed changes: audit report, readiness JSON, minimal compatibility fixes if a
test failure is trivial and unrelated to results.

Forbidden items: new experiments, result edits, deleting negative evidence,
rewriting the project from scratch.

Expected artifacts: `docs/repo_audit_before_level3.md`,
`artifacts/reports/step0_readiness_report.json`.

Acceptance criteria: tests and core checks pass or failures are documented;
protected result files are unchanged.

Failure downgrade strategy: mark Step 0 as `completed_with_failures` and record
blocking risks before any upgrade.

Permission to proceed: proceed to Step 1 only after the repository state and
preservation strategy are documented.

## Step 1: Research Positioning and Claim Boundary

Goal: define the honest research identity, claim boundary, roadmap, legacy
scope, and reporting contract.

Allowed changes: README, docs, claim-boundary docs, Level 3 roadmap, legacy
scope docs, reporting contract docs, claim hygiene phrase list, readiness JSON.

Forbidden items: new experiments, result edits, URD-Selector code, new loaders,
new tokenizers, new baselines, and claims that the project is CCF-B ready.

Expected artifacts: `docs/research_positioning.md`,
`docs/research_questions.md`, `docs/claim_boundary.md`,
`docs/level3_upgrade_roadmap.md`, `docs/legacy_scope.md`,
`docs/reporting_contract_level3.md`,
`artifacts/reports/step1_readiness_report.json`.

Acceptance criteria: claim hygiene passes, main-result purity passes, protected
result files remain unchanged, README no longer dilutes the research mainline.

Failure downgrade strategy: keep the project at `EXPERIMENT-CANDIDATE` and
record unsafe phrases or boundary gaps before Step 2.

Permission to proceed: proceed to Step 2 only after claim hygiene and result
purity checks pass.

## Step 2: Dataset Pipeline Upgrade

Goal: make dataset status, manifests, split integrity, no-fallback checks, and
sample/full-scope boundaries stricter and easier to audit.

Step 2 status after implementation: data-source interface implemented,
token-budget smoke preparation verified, and sample/protocol configs added.
FineWeb, Dolma, and Pile remain protocol-only or optional; full 100M/500M
dataset preparation is not completed.

Allowed changes: dataset manifests, dataset cards, data-loading checks,
reporting around sample versus full scope, no-fallback enforcement, and tests.

Forbidden items: hand-written experimental results, fallback rows in main
results, full-dataset claims without full upstream processing.

Expected artifacts: upgraded dataset manifest schema, split-integrity report,
dataset status matrix, no-fallback report, dataset-scope tests.

Acceptance criteria: every main/cross-dataset row has a clear dataset status,
split scope, source, and fallback flag.

Failure downgrade strategy: mark incomplete datasets as sample or configured
only, never as full.

Permission to proceed: proceed to Step 3 only after data status can be checked
automatically.

## Step 3: Tokenizer Pipeline Upgrade

Goal: separate char-level legacy evidence from future BPE/GPT-style mainline
evidence.

Step 3 status after implementation: tokenizer interface implemented,
char-level tokenizer wrapped as legacy/current evidence, BPE smoke tokenizer
pipeline verified, and GPT-2 wrapper added as optional. BPE16k/BPE32k mainline
tokenizer training is not completed.

Allowed changes: tokenizer manifests, tokenizer config validation, hash tracking,
tests, and documentation.

Forbidden items: claiming BPE mainline completion before verified training rows
exist.

Expected artifacts: tokenizer manifest, tokenizer hash report, tokenizer
compatibility tests, char versus BPE boundary notes.

Acceptance criteria: every result row can be traced to tokenizer type, vocab,
hash, and config.

Failure downgrade strategy: keep char-level as legacy/current evidence and mark
BPE as configured-only.

Permission to proceed: proceed to Step 4 only after tokenizer identity is
machine-checkable.

## Step 4: Strong Baseline and Filter Interface Upgrade

Goal: create a fair interface for raw, random, dedup, length, HDQS++, and future
C4/Gopher/CCNet/perplexity/classifier/embedding-diversity baselines.

Step 4 status after implementation: filter interface implemented, filter
registry added, filter manifests/checker added, keep-rate fairness reports
added, and smoke outputs generated for raw, random, exact dedup, length,
C4-style proxy, Gopher-style proxy, perplexity proxy, and embedding-diversity
proxy. HDQS++ is preserved as a historical baseline/failure-analysis object.
The full strong-baseline matrix is not completed as model evidence.

Allowed changes: filter interface, baseline manifests, keep-rate calibration,
tests, and reporting.

Forbidden items: adding claimed method wins without matched keep-rate, token
budget, and registry support; claiming C4/Gopher/CCNet official reproduction;
claiming neural perplexity/classifier/embedding baselines before real artifacts
exist.

Expected artifacts: baseline registry, filter output manifest, keep-rate
calibration report, fairness tests, and `docs/filter_pipeline_step4.md`.

Acceptance criteria: filter outputs share schema, smoke manifests validate,
proxy/protocol boundaries are explicit, and no Step 4 output enters
`main_results`.

Failure downgrade strategy: label partial baselines as smoke or configured-only.

Permission to proceed: proceed to Step 5 only after baseline output is uniform
and protected result files remain unchanged.

## Step 5: Model Training Pipeline Upgrade

Goal: stabilize the training pipeline before evaluating future methods.

Step 5 status after implementation: model config validation, tokenizer-aware
data adapter, smoke trainer, evaluator, metrics manifest, checkpoint manifest,
training manifest checker, and tiny BPE smoke training are implemented. The
small/medium/large-lite BPE settings remain protocol-only or future work.

Allowed changes: training manifests, checkpoint manifests, multi-seed support,
loss curves, throughput/cost logging, memory logging, tests.

Forbidden items: adding URD-Selector evaluation before the model pipeline is
stable; reporting tiny smoke training as a main result; claiming completed
small/medium/large-lite evidence without registered training runs.

Expected artifacts: checkpoint manifest, training log schema, loss curves,
multi-seed summaries, reproducibility checks.

Acceptance criteria: runs are reproducible across seeds and trace to dataset,
tokenizer, model, filter, and training configs.

Failure downgrade strategy: keep incomplete scale settings as configured-only or
pilot evidence.

Permission to proceed: proceed to Step 6 only after Step 5 tests, manifest
checks, claim hygiene, and main-result purity checks pass.

## Step 6: URD-Selector Implementation

Goal: implement the future Utility-Risk-Diversity selector after data, tokenizer,
baseline, and training layers are stable.

Step 6 status after implementation: URD components, fixed-weight selector,
Pareto-style selector, ablation configs, smoke filter outputs, component scores,
URD summaries, manifests, and manifest checks are implemented. Effectiveness is
not established in Step 6.

Allowed changes: URD scoring modules, selector configuration, Pareto selection,
ablation design, tests, and registered experiments.

Forbidden items: claiming URD effectiveness before fair registered model and
metric results exist; adding PPL/downstream results in this step; treating smoke
selection as main evidence.

Expected artifacts: URD config, score manifest, selection manifest, ablation
plan, registered runs.

Acceptance criteria: URD results can be compared to raw and strong baselines
under equal budgets.

Failure downgrade strategy: keep URD as a failed or partial method if future
evaluation does not support it.

Permission to proceed: proceed to Step 7 after selector smoke outputs and
manifest checks pass.

## Step 7: Evaluation Metric Expansion

Goal: move beyond a single PPL-centric story.

Step 7 status after implementation: evaluation_v2 interfaces, LM smoke wrapper,
downstream protocol matrix, risk/diversity/cost smoke evaluators,
stability/statistics utilities, Pareto smoke evaluator, evaluation manifests,
and manifest checks are implemented. Step 7 does not add canonical result rows
or method-effectiveness evidence.

Allowed changes: risk metrics, diversity metrics, cost metrics, rank stability,
bootstrap confidence intervals, paired tests, and downstream evaluation where
available.

Forbidden items: reporting downstream completion before actual downstream runs;
turning smoke metrics into main evidence; adding a method-effectiveness claim
without registered main experiments.

Expected artifacts: metric reports, CI tables, rank stability analysis, Pareto
frontier tables.

Acceptance criteria: each metric has a script, artifact, and interpretation
boundary.

Failure downgrade strategy: mark missing metrics as protocol or insufficient
evidence, not completed.

Permission to proceed: proceed to Step 8 once smoke/protocol evaluation
manifests validate and protected result files remain unchanged.

## Step 8: Mechanism Analysis

Goal: explain why filters help or fail.

Step 8 status after implementation: analysis_v2 interfaces,
mechanism manifests, evidence-sufficiency checks, proxy-utility,
overfiltering, diversity-loss, domain-shift, Pareto-mechanism smoke
diagnostics, rank/tokenizer/scale protocol analyses, and failure taxonomy are
implemented. Step 8 does not add model training, formal PPL/downstream results,
or full-scale mechanism conclusions.

Allowed changes: proxy-utility mismatch analysis, diversity-loss analysis,
domain-shift analysis, scale-sensitivity analysis, failure-case reports.

Forbidden items: hiding failure cases, deleting negative evidence, reporting
smoke/protocol diagnostics as main evidence, or claiming a mechanism advantage
without registered full evidence.

Expected artifacts: mechanism reports, failure examples, domain-shift figures,
diversity-loss tables.

Acceptance criteria: each major mechanism claim has a required artifact path or
is marked as insufficient evidence/protocol-only.

Failure downgrade strategy: keep findings as hypotheses if mechanism evidence is
insufficient.

Permission to proceed: proceed to Step 9 after mechanism manifests validate and
protected result files remain unchanged.

## Step 9: Artifact Registry, Readiness, and Claim Hygiene Strengthening

Goal: make the release harder to misreport.

Allowed changes: registry schema, artifact index, claim map, readiness reports,
release checks, CI checks.

Forbidden items: lowering checks to pass a weak release.

Expected artifacts: upgraded registry schema, artifact index, claim-support map,
release report, readiness JSON.

Acceptance criteria: release checks pass from a fresh extraction and claims map
to evidence.

Failure downgrade strategy: freeze the release as candidate or incomplete.

Permission to proceed: proceed to Step 10 only after fresh-release verification
passes.

## Step 10: Level 3 Heavy Protocol and Release Freeze

Goal: freeze the heavy protocol and produce a reviewable Level 3 release
candidate.

Allowed changes: final protocol, release notes, archive packaging,
reproducibility report, final checks.

Forbidden items: post-hoc result edits, hand-written main results, and upgraded
readiness labels without evidence.

Expected artifacts: frozen protocol, final registry, final result tables, final
release zip, reproducibility report.

Acceptance criteria: all protected checks pass and claims are supported by
artifacts.

Failure downgrade strategy: release as `EXPERIMENT-CANDIDATE` or `LEVEL3-PILOT`
instead of claiming completion.

Permission to proceed: only a completed Step 10 can support a future
`level3_completed_artifact: true` status.
