# Step 5 Model Training Pipeline

Step 5 adds a tokenizer-aware model training layer for the Level 3 upgrade path.
It is deliberately scoped as infrastructure and smoke verification only. It does
not add a new main result, does not modify existing result tables, and does not
claim that BPE, medium, large-lite, or URD-Selector evidence is complete.

## Purpose

The goal is to make future method comparisons traceable across:

- dataset JSONL and dataset manifest;
- tokenizer manifest and tokenizer hash;
- model config and parameter count;
- training config, seed, budget, and device;
- metrics, loss curve, checkpoint, checkpoint manifest, and training manifest.

This stabilizes the model layer before Step 6 introduces URD-Selector.

## Added Code

The model layer is under `src/models_v2/`:

- `config.py`: JSON-compatible decoder LM config loader.
- `decoder_lm.py`: tiny decoder-only causal LM used for smoke training.
- `parameter_count.py`: deterministic parameter-count estimator.
- `validation.py`: model-family, scale, hidden/head, dropout, and parameter-count checks.

The training layer is under `src/training_v2/`:

- `config.py`: training config schema.
- `data_adapter.py`: Step 2 JSONL plus Step 3 tokenizer-manifest adapter.
- `trainer.py`: small deterministic training loop with loss-curve capture.
- `evaluator.py`: validation loss and PPL helper.
- `checkpoint.py`: checkpoint and checkpoint-manifest writer.
- `manifest.py`: training-manifest writer.
- `registry.py`: Step 5 local training registry writer.
- `validation.py`: training-manifest and main-result isolation checks.

## Smoke Training Artifact

The verified smoke run is:

- dataset: `artifacts/data_step2/wikitext2_smoke/train.jsonl`
- dataset manifest: `artifacts/data_step2/wikitext2_smoke/data_manifest.json`
- tokenizer manifest: `artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json`
- model config: `configs/models_v2/tiny_smoke_bpe.yaml`
- training config: `configs/training/smoke_bpe_tiny.yaml`
- output directory: `artifacts/training_step5/wikitext2_smoke_bpe_tiny`

Produced files:

- `artifacts/training_step5/wikitext2_smoke_bpe_tiny/training_manifest.json`
- `artifacts/training_step5/wikitext2_smoke_bpe_tiny/metrics.json`
- `artifacts/training_step5/wikitext2_smoke_bpe_tiny/checkpoint.pt`
- `artifacts/training_step5/wikitext2_smoke_bpe_tiny/checkpoint_manifest.json`

These files are smoke-only. Their metrics are not main evidence and must not
enter `artifacts/tables/main_results.csv`,
`artifacts/stats/main_results.csv`, or
`artifacts/cross_dataset/cross_dataset_results.csv`.

## Supported Tokenizer Paths

Step 5 supports:

- `lightweight_bpe_smoke`: verified by the BPE smoke run.
- `char`: preserved for legacy/current compatibility and tested with temporary
  unit-test manifests.

GPT-2 and BPE16k/BPE32k remain optional or protocol-only until real tokenizer
manifests and registered training runs exist.

## Model Scale Boundary

Configured model scales:

- `tiny_smoke`: runnable smoke models only.
- `small`: protocol target for future mainline runs.
- `medium_protocol`: configured-only future scale.
- `large_lite_protocol`: configured-only future scale.

Step 5 does not claim completed small/medium/large-lite BPE training evidence.
Those settings remain protocol or future-work entries until actual registered
runs are produced.

## Validation Commands

Run the Step 5 smoke training:

```bash
python scripts/train_model_v2.py \
  --dataset artifacts/data_step2/wikitext2_smoke/train.jsonl \
  --dataset-manifest artifacts/data_step2/wikitext2_smoke/data_manifest.json \
  --tokenizer-manifest artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json \
  --model-config configs/models_v2/tiny_smoke_bpe.yaml \
  --scope smoke \
  --seed 42 \
  --max-steps 2 \
  --batch-size 2 \
  --output-dir artifacts/training_step5/wikitext2_smoke_bpe_tiny \
  --save-checkpoint
```

Validate manifests and result isolation:

```bash
python scripts/check_training_manifests.py --include-step5
python scripts/check_main_results_purity.py
python scripts/check_claim_hygiene.py
```

Run the full local check suite:

```bash
python scripts/run_all_checks.py --timeout 300
```

## Claim Boundary

Safe claims:

- Step 5 implements a tokenizer-aware training interface.
- Step 5 produced a tiny BPE smoke training artifact with manifest, metrics,
  checkpoint, and checkpoint manifest.
- Step 5 keeps smoke artifacts out of canonical main results.
- Step 5 preserves legacy char-level compatibility.

Unsafe current claims:

- BPE mainline training is complete.
- medium or large-lite evidence is complete.
- URD-Selector is evaluated.
- Step 5 smoke PPL is a main result.
- Step 5 does not complete CCF-B-level readiness evidence or Level 3 status.

## Next Step

After Step 5 checks pass, the safe next step is Step 6:
`urd_selector_implementation`. Step 6 should use this stable training contract
instead of adding method evidence directly into legacy result tables.
