# Model Scaling Summary

Mode label: `quick`
Seed setting: not applicable; this is generated from model configs.
Training budget: config-level summary only.
Interpretation: this artifact compares configured character/BPE model sizes and context lengths.
Limitation note: it is not a claim that every model has completed full training.

This table is generated from model configs. It is not a claim that every model has completed full training.

| Model | Tokenizer | Context | Estimated params | Status |
| --- | --- | ---: | ---: | --- |
| `bpe-mini-gpt` | BPETokenizer from course_project_suite.cs336.tokenizer | 32 | 28672 | supported implementation; excluded from CPU quick matrix |
| `bpe_small_gpt` | local BPE tokenizer | 96 | 270336 | paper-prototype dry-run configuration |
| `bpe_tiny_gpt` | local BPE tokenizer | 32 | 28672 | implementation available; excluded from default CPU quick run |
| `char-mini-gpt` | character | 32 | 16384 | configured |
| `char_small_gpt` | character | 64 | 106496 | paper-prototype small-run configuration |
| `char_tiny_gpt` | character | 32 | 9984 | quick-mode supported |
| `medium-gpt-optional` | character or BPE | 128 | 851968 | optional CUDA-oriented extension; not run in CI |
| `optional_bpe_medium_gpt` | local BPE tokenizer | 128 | 851968 | optional CUDA-oriented extension; not run in CI |
| `small-gpt-debug` | character | 64 | 106496 | configured |
