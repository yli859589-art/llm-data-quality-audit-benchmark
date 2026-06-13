# Dataset Pipeline Step 2

## Purpose

Step 2 upgrades the data layer only. It adds a unified data-source interface,
token-budget sampling, manifest generation, and no-fallback validation so later
steps can build tokenizer, baseline, training, and URD-Selector work on a
cleaner data foundation.

Step 2 does not add tokenizer code, model training, baseline/filter methods,
URD-Selector, downstream metrics, or new experiment results.

## Existing Data Assets Preserved

The upgrade preserves the existing data assets:

- WikiText-2 official-split real non-fallback data.
- OpenWebText bounded streaming-sample audit evidence.
- C4 English bounded streaming-sample audit evidence.
- Existing `artifacts/data/*/data_manifest.json` files.
- Existing dataset cards.
- Existing split-integrity and no-fallback checks.
- Existing `scripts/prepare_real_data.py`.
- Existing `scripts/prepare_streaming_data.py`.
- Existing cross-dataset artifacts.

No existing data manifest or negative result is deleted by Step 2.

## New Data Source Interface

Step 2 adds `src/data_sources/` with:

- `DatasetSourceConfig`
- `DatasetSource`
- `DatasetSplit`
- `DatasetRecord`

Each record has:

- `doc_id`
- `text`
- `source`
- `split`
- `metadata`

Each source supports:

- `iter_records()`
- `prepare()`
- `estimate_tokens()`
- `write_jsonl()`
- `write_manifest()`

The interface bridges current local/streaming artifacts without replacing the
legacy preparation scripts.

## Token-Budget Policy

Step 2 supports:

- `full`
- `1K`
- `10K`
- `1M`
- `50M`
- `100M`
- `500M`
- `1B`
- integer budgets

Sampling is deterministic with a seed. It can preserve document order or use
shuffle plus seed. Token counting is a proxy in Step 2:

- `whitespace`
- `character`
- `unknown`
- `future_bpe`

Current Step 2 manifests must record the proxy token counter type. Proxy counts
must not be reported as BPE counts. Step 3 is responsible for tokenizer pipeline
upgrades.

## Manifest Schema

Step 2 manifests use:

`manifest_version = step2.dataset_manifest.v1`

Required fields include dataset identity, split, source kind, scope, requested
and numeric token budget, actual estimated tokens, token counter type, document
count, seed, shuffle flag, fallback flags, smoke/protocol flags, output hash,
output path, loader identity, upstream id, license note, and notes.

Rules:

- `main` and `heavy` must use `allow_fallback=false`.
- `fallback_used=true` cannot enter `main` or `heavy`.
- `smoke` must set `smoke_only=true`.
- `implemented_but_not_run=true` must not claim a fake output path.
- `data_hash` is based on the actual output JSONL content when output exists.

## Fallback Policy

Step 2 separates fallback/smoke behavior from main evidence:

- Smoke fixtures are allowed only with `scope=smoke` and `smoke_only=true`.
- Sample protocol can use existing real cached data only when available.
- Main/heavy configs must not allow fallback.
- Protocol-only datasets must be marked `implemented_but_not_run` or
  `optional_remote`, not completed.

## Scope Labels

- `smoke`: offline fixture path for tests and local verification.
- `sample`: bounded real sample or existing cached sample.
- `main`: future main dataset scope, no fallback allowed.
- `heavy`: future heavy dataset scope, no fallback allowed.
- `implemented_but_not_run`: protocol exists, but data has not been prepared.

## Implemented-But-Not-Run

`implemented_but_not_run` means the loader protocol, config, and manifest path
exist, but no completed dataset output is claimed. It is not a failed result and
not a completed result. It prevents future plans from being misreported as
evidence.

## Dataset Status

| Dataset | Step 2 status | Safe interpretation |
|---|---|---|
| WikiText-2 | smoke verified; local official-split bridge implemented | Existing official-split evidence is preserved; Step 2 smoke output is not main evidence. |
| OpenWebText | local cached streaming-sample bridge implemented | Existing bounded streaming-sample audit evidence only. |
| C4 English | local cached streaming-sample bridge implemented | Existing bounded streaming-sample audit evidence only. |
| FineWeb | protocol/optional loader implemented | No real FineWeb 100M/500M data prepared in Step 2. |
| Dolma | protocol/optional loader implemented | No real Dolma 100M/500M data prepared in Step 2. |
| Pile subset | protocol/optional loader implemented | No real Pile subset data prepared in Step 2. |

## What Step 2 Actually Ran

Step 2 ran a WikiText-2 smoke preparation command:

```bash
python scripts/prepare_data_v2.py --dataset wikitext2 --split train --scope smoke --token-budget 10K --seed 42 --output artifacts/data_step2/wikitext2_smoke/train.jsonl --manifest-output artifacts/data_step2/wikitext2_smoke/data_manifest.json
```

The generated smoke manifest is under:

- `artifacts/data_step2/wikitext2_smoke/data_manifest.json`

This output is explicitly `scope=smoke` and `smoke_only=true`.

## What Step 2 Did Not Run

Step 2 did not run:

- FineWeb real 100M/500M preparation.
- Dolma real 100M/500M preparation.
- Pile real preparation.
- Full upstream OpenWebText preparation.
- Full upstream C4 preparation.
- Model training.
- Tokenizer upgrades.
- Baseline/filter experiments.
- URD-Selector.

## Why This Is Not Full Level 3 Data Completed

Step 2 adds the data pipeline interface and smoke verification. It does not
prepare the full heavy datasets, does not validate BPE token budgets, does not
run model-scale training, and does not complete the Level 3 data matrix.

Therefore the project remains:

- `ccf_b_ready: false`
- `level3_pipeline_ready: false`
- `level3_completed_artifact: false`

## Next Step

Next step: `step3_tokenizer_pipeline_upgrade`.

Step 3 should connect tokenizer identity and future BPE manifests. Step 2 proxy
token counts must remain labeled as proxy counts until then.
