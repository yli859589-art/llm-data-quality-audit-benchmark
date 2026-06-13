# LocalMax Results

Current status: `LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED`

Level 3 status: `not completed`

This document summarizes the frozen LocalMax evidence generated from Step 10B artifacts.

## Evidence Matrix

- Datasets: `2`.
- Methods: `4`.
- Seeds: `3`.
- Strengthened runs: `24`.
- Metric for method comparison: `valid_loss`.
- PPL status: clipped for this run and not comparable across methods.

## Dataset Scale

- `openwebtext_20m`: `20002346` GPT-2 tokens, `17705` documents
- `c4_en_20m`: `20005050` GPT-2 tokens, `42457` documents

## URD-Fixed Disclosure

- `c4_en_20m`: mean paired valid_loss delta `-0.04633625348409017`, CI [`-0.2861620783805847`, `0.19348957141240436`], crosses zero `True`
- `openwebtext_20m`: mean paired valid_loss delta `0.3360164016485214`, CI [`-0.07903489470481873`, `0.7510676980018616`], crosses zero `True`

URD-fixed evidence is mixed in this LocalMax release.

On OpenWebText 20M, URD-fixed has a lower mean valid_loss than raw in this local run, but the confidence interval crosses zero. On C4 English 20M, URD-fixed does not improve over raw by valid_loss.

## Claim Boundary Statement

The current LocalMax evidence does not support a claim that URD-fixed outperforms raw.
