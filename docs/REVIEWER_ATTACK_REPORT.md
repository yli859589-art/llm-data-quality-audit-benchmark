# Reviewer Attack Report

## Attack 1: Is this just a module collection?

The project now has a clearer research spine: data-quality interventions for
language-model pretraining. The original educational modules remain supporting
implementation evidence, while the main experiment path is represented by
data configs, manifests, baselines, frozen HDQS++, ablations, statistics, and
claim checks.

## Attack 2: Are toy data results being presented as real-data results?

The new configs separate smoke/dev from paper/full. Smoke configs may use
explicitly labeled fallback fixtures. Paper/full configs set
`allow_fallback=false` and `required_real_data=true`; the check script fails if
that boundary is violated.

## Attack 3: Are baselines too weak?

The baseline suite now includes raw, random same keep-rate, length, heuristic
web-quality, exact dedup, n-gram proxy, independent quality score, and optional
external-wrapper slots. This is enough for experiment infrastructure, but
paper claims still need real validation/perplexity metrics.

## Attack 4: Is HDQS++ tuned on test data?

The frozen protocol writes deterministic train/dev/test hashes and records a
no-test-leakage policy. Paper templates remain unexecuted until real corpora
are available.

## Attack 5: Are the statistics meaningful?

The significance analyzer refuses to turn retention-only or one-seed evidence
into model-quality claims. It classifies insufficient evidence as unsupported
or trend-only.

## Attack 6: What would still fail a strict review?

The largest missing pieces are non-fallback real-data preparation, multi-seed
training on larger models, final held-out evaluation, compute logs, and a
formal error-analysis section grounded in real corpus failures.
