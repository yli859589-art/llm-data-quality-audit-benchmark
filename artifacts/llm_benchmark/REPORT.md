# LLM Data Quality and Efficient Attention Benchmark

## Research question

How much do deterministic data-quality controls improve a compact language-model training corpus, and how do reference attention implementations compare on correctness, throughput, and estimated memory?

## Public corpus

- Source: [https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt](https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt)
- SHA-256: `86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed`
- Corpus characters: `1115394`

The training subset is derived from Tiny Shakespeare. The benchmark injects deterministic web-style and symbol-heavy OCR/template noise to create a controlled data-quality stress test. Validation text remains clean and held out.

## Result summary

- The full data-quality pipeline reduced duplicate rate from `0.090` to `0.000` and removed all injected email and phone hits.
- Compared with the raw noisy baseline, the full pipeline reduced held-out validation loss by `2.94%` and perplexity by `10.29%`.
- At sequence length `128`, PyTorch SDPA achieved `3.77x` the naive reference throughput with an estimated working-set reduction of `50.0%`.
- Cleaning and redaction alone are not sufficient: the ablation retains duplicated and symbol-heavy documents, so filtering and deduplication remain necessary.

## Data-quality ablation

| Variant | Documents | Characters | Duplicate rate | Email hits | Phone hits | Quality pass rate |
|---|---:|---:|---:|---:|---:|---:|
| `raw_noisy_baseline` | 310 | 107118 | 0.090 | 24 | 24 | 0.542 |
| `clean_redact` | 310 | 102863 | 0.090 | 0 | 0 | 0.542 |
| `deduplicate_only` | 282 | 96305 | 0.000 | 20 | 20 | 0.496 |
| `quality_filter_only` | 168 | 64707 | 0.167 | 24 | 24 | 1.000 |
| `full_pipeline` | 140 | 50789 | 0.000 | 0 | 0 | 1.000 |

## Character-level GPT ablation

| Variant | Final validation loss | Validation perplexity | Training characters | Tokens/s |
|---|---:|---:|---:|---:|
| `raw_noisy_baseline` | 3.6923 | 40.14 | 52000 | 12863.1 |
| `clean_redact` | 3.7750 | 43.60 | 52000 | 14036.6 |
| `full_pipeline` | 3.5837 | 36.00 | 51067 | 13506.0 |

![Training curves](training_curves.svg)

## Attention systems benchmark

| Implementation | Sequence length | Query tokens/s | Max error vs. naive | Estimated working set bytes | CUDA peak bytes |
|---|---:|---:|---:|---:|---:|
| `naive` | 32 | 31836.8 | 0.00e+00 | 40960 | N/A |
| `online_reference` | 32 | 28311.7 | 4.77e-07 | 40960 | N/A |
| `torch_sdpa` | 32 | 170985.8 | 5.96e-07 | 32768 | N/A |
| `naive` | 64 | 84875.0 | 0.00e+00 | 98304 | N/A |
| `online_reference` | 64 | 61241.1 | 3.58e-07 | 98304 | N/A |
| `torch_sdpa` | 64 | 342612.4 | 4.17e-07 | 65536 | N/A |
| `naive` | 128 | 134687.2 | 0.00e+00 | 262144 | N/A |
| `online_reference` | 128 | 87560.3 | 4.17e-07 | 262144 | N/A |
| `torch_sdpa` | 128 | 507332.5 | 5.36e-07 | 131072 | N/A |

![Attention throughput](attention_throughput.svg)

## Error analysis

- Removed documents: `170`
- Note: Examples are redacted before reporting and may include duplicates or quality-filter failures.

- Sanitized removed example: `@@@@ #### $$$$ !!!! **** 93 @@@@ #### $$$$ !!!! **** 93 @@@@ #### $$$$ !!!! **** 93 @@@@ #### $$$$ !!!! **** 93 @@@@ #### $$$$ !!!! **** 93 @@@@ #### $$$$ !!!! **** 93 @@@@ #### $$`
- Sanitized removed example: `@@@@ #### $$$$ !!!! **** 85 @@@@ #### $$$$ !!!! **** 85 @@@@ #### $$$$ !!!! **** 85 @@@@ #### $$$$ !!!! **** 85 @@@@ #### $$$$ !!!! **** 85 @@@@ #### $$$$ !!!! **** 85 @@@@ #### $$`
- Sanitized removed example: `@@@@ #### $$$$ !!!! **** 34 @@@@ #### $$$$ !!!! **** 34 @@@@ #### $$$$ !!!! **** 34 @@@@ #### $$$$ !!!! **** 34 @@@@ #### $$$$ !!!! **** 34 @@@@ #### $$$$ !!!! **** 34 @@@@ #### $$`

## Limitations

- Tiny Shakespeare is a compact public corpus, not a production-scale web dataset.
- Injected stress-test corruption makes the quality experiment reproducible but does not estimate the natural noise rate of a production web corpus.
- CPU memory values are algorithmic estimates. CUDA peak allocation is reported only when CUDA is used.
- The online attention implementation is a numerically stable reference, not a fused production kernel.
