# Tokenizer Pipeline Step 3

## Purpose

Step 3 upgrades the tokenizer layer only. It adds a unified tokenizer interface,
tokenizer manifests, tokenizer hashes, optional GPT-2 wrapper support, and
tokenizer-specific token-budget checks.

Step 3 does not add baseline/filter methods, URD-Selector, model training,
evaluation metrics, mechanism analysis, or new experiment results.

## Current Char-Level Tokenizer Status

The current main evidence path uses a shared character vocabulary through
`CharVocab` in `src/course_project_suite/llm_benchmark/char_lm.py`. That path is
preserved because it supports the existing small-model audit evidence and should
not be deleted.

However, char-level tokenization is now explicitly marked as legacy/current
evidence and smoke-compatible infrastructure. It is not the future Level 3
modern tokenizer mainline.

## Why Char-Level Is Not Level 3 Mainline

Character tokenization is useful for fast, deterministic small-model experiments,
but it is not comparable to modern LLM pretraining tokenization. It changes
sequence lengths, token budgets, vocabulary size, and model efficiency. Level 3
main experiments must use tokenizer-specific budgets and a stronger tokenizer
protocol.

## New Tokenizer Interface

Step 3 adds `src/tokenization/`:

- `BaseTokenizer`
- `TokenizerConfig`
- `TokenizerManifest`
- `CharTokenizer`
- `LightweightBPETokenizer`
- `GPT2OptionalTokenizer`

The interface supports:

- `train(texts)`
- `encode(text)`
- `decode(ids)`
- `save(path)`
- `load(path)`
- `vocab_size`
- `tokenizer_id`
- `tokenizer_type`
- `tokenizer_hash`
- `count_tokens(text)`
- `write_manifest(path)`

## BPE Tokenizer Support

Step 3 includes a deterministic lightweight BPE smoke tokenizer. It is used when
SentencePiece/HuggingFace tokenizers are not configured for the local smoke
run. The generated smoke tokenizer is labeled:

- `tokenizer_type: lightweight_bpe_smoke`
- `scope: smoke`
- `smoke_only: true`
- `level3_mainline: false`

BPE16k and BPE32k are represented as protocol configs only. They are not trained
as mainline tokenizers in Step 3.

## GPT-2 Optional Wrapper

`GPT2OptionalTokenizer` can use `tiktoken` or local `transformers` assets if
available. If the dependency or local files are unavailable, it reports graceful
unavailable status. Tests do not download GPT-2 and do not require network.

An unavailable GPT-2 wrapper must be represented as optional or
implemented-but-not-run. It must not claim completed tokenizer evidence.

## Tokenizer Manifest Schema

Step 3 manifests use:

`manifest_version = step3.tokenizer_manifest.v1`

Required fields include tokenizer name/type, scope, Level 3 mainline flag,
requested and actual vocab size, training data path/hash, training scope, seed,
normalization, model/vocab paths, tokenizer hash, optional dependency status,
fallback status, smoke flag, implemented-but-not-run flag, and notes.

## Tokenizer Hash Policy

Tokenizer hashes are based on tokenizer model/vocab/config content. Smoke BPE
artifacts save a tokenizer JSON and vocab JSON. Protocol-only or unavailable
optional tokenizers must not claim model or vocab paths.

## Token-Budget Fairness Policy

Step 2 whitespace counts are proxy counts. Step 3 tokenizer counts are
tokenizer-specific. They must not be mixed as equal training budgets.

Future Level 3 main experiments must define the main tokenizer first and enforce
token budgets using that tokenizer. Char-level token counts and BPE token counts
are not directly interchangeable.

## Scope Labels

- `smoke`: local verification artifact; not main evidence.
- `sample`: future sample tokenizer run.
- `main_protocol`: protocol exists but mainline training is not completed.
- `legacy_current`: current historical char-level evidence.
- `implemented_but_not_run`: wrapper/protocol exists, no completed artifact.

## What Step 3 Actually Ran

Step 3 runs a smoke BPE tokenizer command:

```bash
python scripts/train_tokenizer_v2.py --tokenizer-type bpe --name bpe_smoke_512 --data artifacts/data_step2/wikitext2_smoke/train.jsonl --scope smoke --vocab-size 512 --seed 42 --output-dir artifacts/tokenizers_step3/bpe_smoke --manifest-output artifacts/tokenizers_step3/bpe_smoke/tokenizer_manifest.json --allow-fallback
```

It also runs tokenizer manifest validation and a tokenizer-specific budget
report for that smoke tokenizer.

## What Step 3 Did Not Run

Step 3 did not run:

- BPE16k or BPE32k mainline tokenizer training.
- GPT-2 tokenizer download.
- LM training with BPE.
- Medium model training.
- Baseline/filter experiments.
- URD-Selector.
- Downstream, risk, diversity, or cost evaluation.

## Why This Is Not BPE Mainline Completed Evidence

The smoke tokenizer proves the pipeline and manifest path. It does not prove a
modern tokenizer mainline, does not train a large BPE vocabulary, and does not
produce model results. It must not be used as completed Level 3 tokenizer
evidence.

Current status remains:

- `ccf_b_ready: false`
- `level3_pipeline_ready: false`
- `level3_completed_artifact: false`

## Next Step

Next step: `step4_strong_baseline_filter_interface_upgrade`.

Step 4 may add stronger baseline/filter interfaces. It should use the tokenizer
manifest and budget policies introduced here, but it should not reinterpret
Step 3 smoke artifacts as mainline model evidence.
