# LocalMax Release Freeze

Current status: `LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED`

Level 3 status: `not completed`

This release freezes the Step 10B LocalMax minimal training evidence into a reviewable research artifact. It does not run new training, does not expand data, and does not add new methods.

Bundle scope: `standalone_metadata_bundle`.

The `artifacts/localmax_release/` directory is a standalone metadata bundle for review. It includes release tables, figures, reports, dataset/tokenizer/filter/training/evaluation metadata, metrics, lineage, and state fingerprints. It does not include raw data text or full binary checkpoints.

## Scope

- Datasets: `2` local non-fallback 20M-token samples.
- Methods: `raw`, `exact_dedup`, `length_filter`, `urd_fixed`.
- Seeds: `13`, `42`, `101`.
- Strengthened training runs: `24`.
- Minimum training strength: `100` steps and `25600` tokens seen per completed run.
- Model scale: `small`; parameter count `20505888`.
- Tokenizer: GPT-2 BPE tokenizer.
- Primary comparison metric: `valid_loss`.
- PPL is clipped and not comparable for improvement claims.

## Why This Is Not Level 3

This release is a local minimal training-evidence artifact. It does not include cloud-scale 500M-token data per dataset, true medium-model runs, selected large-lite runs, official downstream evaluation, or a full mechanism study.

## Reproduction

Run:

```bash
python scripts/localmax/finalize_localmax_release.py
python scripts/localmax/check_localmax_release_claims.py
python -m pytest tests/ -q
```

The release tables and figures are derived from Step 10B artifacts under `artifacts/localmax_tables/`, `artifacts/localmax_training_strengthened/`, `artifacts/localmax_evaluation_strengthened/`, and `artifacts/localmax_analysis_strengthened/`.

Figures are regenerated from release CSV tables. Step 10C-hotfix only improves release quality, figure readability, and cross-platform reproducibility; all experimental values are unchanged.
