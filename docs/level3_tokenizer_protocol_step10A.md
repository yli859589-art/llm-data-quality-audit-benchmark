# Level 3 Tokenizer Protocol Step 10A

The Level 3 tokenizer protocol moves the future mainline away from char-level
evidence and toward BPE or GPT-2-compatible token budgets.

## Mainline Tokenizers

- `gpt2`
- `bpe16k`
- `bpe32k`

Each mainline tokenizer must have a manifest, vocabulary hash, and tokenizer
specific token-count method. Trained BPE tokenizers must also record the
training data hash.

## Legacy Boundary

`char_legacy` and `lightweight_bpe_smoke` remain useful for historical and smoke
checks, but they are not Level 3 mainline tokenizers.

## Future Artifacts

- `artifacts/level3_tokenizers/*/tokenizer_manifest.json`
- `artifacts/level3_tokenizers/*/vocab_hash.txt`
- `artifacts/level3_tokenizers/*/token_budget_report.json`

