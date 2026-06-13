# LocalMax Limitations

Current status: `LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED`

Level 3 status: `not completed`

This release is useful as local-scale evidence, not as a finished conference-level benchmark.

## Main Limitations

- Only two datasets are included.
- Each dataset is a 20M GPT-2-token local sample, not a 500M-token heavy benchmark.
- Only four methods are included.
- The completed training evidence is small-model evidence.
- A true medium run has not been completed.
- No selected large-lite run has been completed.
- Official downstream evaluation has not been run.
- PPL is clipped and should not be used for method comparison.
- Comparisons use `valid_loss`.
- The training token budget remains small relative to the future cloud route.
- The release cannot claim Level 3 completion or CCF-B-level readiness.
- Step 10C-hotfix only improves release quality and reproducibility. It does not change experimental results.
