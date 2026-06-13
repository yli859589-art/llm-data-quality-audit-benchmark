# Claim Boundary

This document defines what the repository can and cannot claim after Step 1.
It complements `docs/REPORTING_CONTRACT.md`,
`docs/reporting_contract_level3.md`, and the canonical status document
`docs/PROJECT_STATUS.md`.

## Current Status

- historical_release_readiness: `EXPERIMENT-CANDIDATE`
- level3_route_readiness: `LEVEL3_PIPELINE_READY`
- method_status: `honest_audit_framework`
- benchmark_scope_status: `multi_dataset_audit_candidate`
- ccf_c_ready: `false`
- ccf_b_ready: `false`
- level3_pipeline_ready: `true`
- level3_completed: `false`

## Allowed Current Claims

The repository may currently claim:

- an experiment-candidate audit benchmark for LLM data-quality filtering;
- real non-fallback WikiText-2 official-split evidence;
- bounded streaming-sample audit evidence for OpenWebText/C4;
- raw, random same keep-rate, dedup, length, and HDQS++ comparisons inside the
  recorded dataset scopes;
- negative evidence that HDQS++ v3 does not outperform raw in the current fair
  WikiText-2 setting;
- artifact lineage, run registry, main-result purity checks, and claim hygiene;
- Level 3 readiness gates, claim map, and artifact registry v2;
- not CCF-C ready and not CCF-B ready;
- a research-artifact upgrade candidate, not a completed CCF-B project.

## Forbidden Current Claims

The following are forbidden current claims unless later evidence explicitly
supports them:

- forbidden current claim: SOTA data filtering;
- forbidden current claim: state-of-the-art data filtering;
- forbidden current claim: HDQS++ beats raw;
- forbidden current claim: HDQS++ outperforms raw;
- forbidden current claim: full OpenWebText benchmark completion;
- forbidden current claim: full C4 benchmark completion;
- forbidden current claim: CCF-B ready;
- forbidden current claim: CCF-A ready;
- forbidden current claim: URD-Selector verified;
- forbidden current claim: downstream evaluation completed;
- forbidden current claim: large-scale LLM pretraining completed;
- forbidden current claim: BPE mainline completed;
- forbidden current claim: medium or large-lite completed evidence;
- forbidden current claim: full Level 3 completed.

These phrases may appear in forbidden-claim or roadmap contexts only. They must
not appear as achievements.

## Future Claims Allowed Only After Evidence

The following claims are allowed only after completed implementation, registered
runs, reproduced artifacts, and claim-hygiene review:

- URD-Selector implemented and evaluated;
- BPE mainline completed;
- medium-scale replicated evidence completed;
- downstream evaluation completed;
- Level 3 pipeline ready;
- future-only claim: Level 3 completed artifact;
- full upstream dataset result;
- stronger baseline matrix completed.

## Result Boundary

`artifacts/tables/main_results.csv` and `artifacts/stats/main_results.csv` are
canonical result artifacts. They must not be hand-written, and they must trace to
registry rows and scripts.

Smoke, fallback, failed, debug, configured-only, and future-protocol rows cannot
be promoted into main-result claims. Negative and failed results must be kept.

## Resume and Portfolio Boundary

Safe resume wording:

> Built a reproducible LLM data-quality audit benchmark with real WikiText-2
> official-split evidence, bounded OpenWebText/C4 streaming-sample audits,
> artifact lineage, claim hygiene checks, and negative-result analysis.

Unsafe resume wording:

> Forbidden claim example: built a verified SOTA filter that beats raw data across full OpenWebText/C4 and
> is CCF-B ready.

The unsafe sentence is included only as a forbidden-claim example.
