# Level 3 Heavy Route

The project route is now a Level 3 route. Step 9 hardens the artifact,
readiness, and claim-hygiene system that protects the route. It does not run the
heavy experiments and does not complete the Level 3 artifact.

## Current State

Current readiness after Step 10A-hotfix is at most `LEVEL3_PIPELINE_READY`.

That means the repository has the pipeline, interfaces, manifests, checkers,
claim boundaries, registry scaffolding, and release gates needed before heavy
execution. It does not mean the heavy evidence exists.

Current forbidden claim: Level 3 completed.

## Route

Step 10A freezes the Level 3 heavy protocol.

Step 10A-hotfix hardens the reproducibility plumbing around that protocol:
artifact scanning is based on repo-relative paths, parent directory names cannot
pollute step detection, and artifact registry finalization runs after generated
reports.

Step 10B is the first step allowed to execute real heavy experiments. The
minimum Level 3 data target is at least three real large datasets, each with at
least 500M tokenizer-specific BPE tokens. A stronger target is 1B BPE tokens per
dataset.

Step 10C can freeze a completed Level 3 artifact only if Step 10B produced real
heavy data, training, evaluation, mechanism, registry, and claim-map evidence.

If Step 10B is not completed, the project must remain at
`LEVEL3_PIPELINE_READY` or lower.

## Required Heavy Evidence

- real 500M-token-or-larger BPE datasets;
- GPT-2 or BPE16k/BPE32k mainline tokenizer manifests;
- full baseline and filter matrix on Level 3 data;
- small, medium, and selected large-lite model runs;
- at least three official downstream benchmarks;
- LM/risk/diversity/cost/stability/Pareto evaluation;
- full-scale mechanism analysis;
- registry-to-result-table traceability;
- claim map entries that point to evidence.

## Boundary

Step 9 may say the pipeline is ready for heavy protocol freezing. Step 10A may
say the heavy protocol is frozen. Neither step may say the heavy route is
completed.

Registry hash mismatch is treated as a reproducibility failure. Reports that
write artifacts must run before artifact registry finalization.
