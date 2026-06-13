# Level 3 Heavy Requirements

Level 3 is an execution standard, not a documentation label.

## Data

- At least three real large datasets.
- At least 500M tokenizer-specific BPE tokens per dataset.
- Strong target: 1B BPE tokens per dataset.
- No fallback data.
- Dataset manifest hash, license/scope note, and split-integrity evidence.

## Tokenizer

- GPT-2 tokenizer or BPE32k mainline.
- BPE16k/BPE32k manifests where applicable.
- Tokenizer-specific token budget.
- Char and lightweight BPE smoke tokenizers are not Level 3 mainline evidence.

## Filters

The full matrix must include raw, random same keep-rate, exact dedup,
near-dedup, length, C4-style, Gopher-style, CCNet-style/proxy, perplexity,
embedding/diversity selector, HDQS++ historical, URD fixed, URD Pareto, and URD
ablations where feasible.

## Models

Tiny smoke runs are not Level 3 evidence. Level 3 requires real small, medium,
and selected large-lite training runs with checkpoint and training manifests.

## Evaluation and Mechanism

Level 3 requires LM metrics, official downstream benchmarks, risk/diversity/cost
metrics, stability/statistics, Pareto analysis, and full-scale mechanism
analysis.

