# Step 8 Mechanism Analysis Pipeline

Step 8 adds a mechanism-analysis layer for the DataAudit-LM / URD-Selector
upgrade path. Its job is to explain how a data filter might fail, why a proxy
score can diverge from actual utility, and what evidence would be required
before making a stronger research claim.

This step implements analysis infrastructure and smoke/protocol diagnostics. It
does not run model training, does not add formal PPL or downstream results, and
does not allow a full-scale mechanism conclusion.

## Why Mechanism Analysis Matters

A serious data-filtering artifact cannot stop at one validation metric. A filter
may appear plausible while hurting utility through overfiltering, losing
diversity, shifting the distribution, depending on tokenizer quirks, or behaving
differently across model scales. Step 8 turns those risks into auditable
diagnostic hooks. That makes later Level 3 heavy-route work easier to review because every
mechanism claim must point to a concrete artifact.

## Architecture

The implementation lives under `src/analysis_v2/`.

- `base.py`: mechanism config, input, result, and base analyzer contracts.
- `schema.py`: valid scopes, analysis types, manifest version, protected files.
- `evidence.py`: evidence sufficiency policy and claim gating.
- `manifest.py`: `mechanism_manifest.json` generation with SHA256 hashes.
- `validation.py`: manifest checker and no-main-results-pollution guard.
- `proxy_utility.py`: proxy-utility mismatch smoke diagnostics.
- `overfiltering.py`: keep-rate/token-retention diagnostics.
- `diversity_loss.py`: lexical/hash diversity diagnostics and unavailable flags.
- `domain_shift.py`: length/token/source shift proxy diagnostics.
- `rank_stability.py`: protocol-only ranking stability plan.
- `tokenizer_sensitivity.py`: protocol-only tokenizer sensitivity plan.
- `scale_trend.py`: protocol-only tiny/small/medium/large-lite scale plan.
- `failure_taxonomy.py`: observed, hypothesized, and protocol-only failure modes.
- `pareto_mechanism.py`: smoke Pareto tradeoff diagnostics.

The command entry point is `scripts/run_mechanism_analysis_v2.py`. The manifest
checker is `scripts/check_mechanism_manifests.py`.

## Manifest Schema

Each output directory contains `mechanism_manifest.json` with:

- `manifest_version`: `step8.mechanism_manifest.v1`
- `analysis_type`: one of the Step 8 mechanism analyses
- `scope`: `smoke`, `sample`, `main_protocol`, `level2_protocol`,
  `level3_heavy_protocol`, or `completed_run`
- `smoke_only` / `protocol_only`
- input artifact paths and SHA256 hashes
- diagnostic table/report paths and SHA256 hashes
- optional figure and extra-output hashes
- `evidence_sufficiency`
- `insufficient_evidence`
- `claim_allowed: false`
- `main_results_modified: false`

The checker rejects missing hashes, unsupported analysis types, unsafe claim
flags, smoke/protocol flag mismatches, and leakage into protected result files.

## Evidence Sufficiency Policy

Step 8 uses `src/analysis_v2/evidence.py` to classify evidence:

- smoke outputs: `smoke_diagnostic_only`
- protocol outputs: `protocol_only`
- small samples without enough evidence: `insufficient`
- future completed runs may become `sufficient`, but Step 8 still defaults to
  `claim_allowed: false`

Any unsupported mechanism claim must remain blocked until future registered
artifacts exist.

## Analyzer Policies

Proxy-utility mismatch analysis links URD/filter component scores to available
smoke LM diagnostics. Because no per-document utility target exists, the current
output marks `insufficient_evidence: true`.

Overfiltering analysis reports document keep-rate, token keep-rate, retained
token counts, and smoke-only warnings. It can flag potential risks but does not
make a formal overfiltering conclusion.

Diversity loss analysis reports lexical diversity, unique-token ratio, entropy
proxy availability, and source/semantic metadata gaps. Without source/domain
metadata or embedding evidence, it cannot support a semantic diversity claim.

Domain shift analysis reports length and token-distribution proxy shifts. Source
or domain shift is explicitly marked unavailable when metadata is missing.

Rank stability, tokenizer sensitivity, and scale trend are protocol-only in this
step. They record the future evidence matrix needed for multi-seed, formal
tokenizer, and multi-scale conclusions.

Failure taxonomy records observed, hypothesized, protocol-only, and
insufficient-evidence failure modes. It preserves the historical negative result
that HDQS++ v3 did not outperform raw under the current historical fair
benchmark evidence.

Pareto mechanism analysis reads Step 6/7 Pareto artifacts as smoke diagnostics
only. It does not claim Pareto frontier improvement.

## What Step 8 Actually Ran

Step 8 generated smoke diagnostics for:

- proxy-utility mismatch
- overfiltering
- diversity loss
- domain/distribution shift
- Pareto mechanism
- failure taxonomy

Step 8 generated protocol-only outputs for:

- rank stability
- tokenizer sensitivity
- scale trend

All outputs are under `artifacts/analysis_step8/` and have mechanism manifests.

## What Step 8 Did Not Run

Step 8 did not:

- train any model
- add formal PPL results
- add official downstream results
- update `artifacts/tables/main_results.csv`
- update `artifacts/stats/main_results.csv`
- update `artifacts/cross_dataset/cross_dataset_results.csv`
- prove URD effectiveness
- prove a full-scale proxy-utility mismatch
- prove tokenizer sensitivity or scale trends
- claim Pareto frontier improvement

## Step 9 and Step 10 Boundary

Step 9 should harden artifact readiness, release checks, registry metadata, and
claim hygiene around the Step 8 outputs. Step 10 should define or freeze the
heavier Level 3 protocol. Step 8 itself remains an infrastructure and
smoke/protocol-diagnostic step.

## Claim Boundary

Safe wording:

- Step 8 implements mechanism-analysis infrastructure.
- Step 8 produces smoke/protocol diagnostic artifacts.
- Step 8 records insufficient-evidence warnings where evidence is not enough.
- Step 8 preserves historical negative results.

Unsafe wording:

- forbidden claim: URD effectiveness is established
- forbidden claim: URD improves PPL or downstream metrics
- forbidden claim: a full-scale mechanism advantage is established
- forbidden claim: tokenizer sensitivity or scale trend is completed
- forbidden claim: the project is CCF-B ready
- forbidden claim: Level 3 is completed
