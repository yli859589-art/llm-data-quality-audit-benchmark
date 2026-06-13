# Level 3 Filter and Baseline Protocol Step 10A

The filter protocol requires all methods to run under matched keep-rate,
dataset, tokenizer, and method-family controls.

## Required Families

- Raw baseline.
- Random same keep-rate baseline.
- Exact deduplication.
- MinHash near deduplication.
- Length filter.
- C4-style, Gopher-style, and CCNet-style proxy heuristics.
- Perplexity filter.
- Classifier quality proxy.
- Embedding-diversity selector.
- HDQS++ as a historical/failure-analysis baseline.
- URD fixed, URD Pareto, and URD component ablations.

## Boundary

Proxy filters must not be described as official C4/Gopher/CCNet reproductions.
URD variants must not be described as effectiveness-verified until future
training and evaluation evidence exists.

## Future Artifacts

- `artifacts/level3_filters/*/filter_manifest.json`
- `artifacts/level3_filters/*/keep_rate_report.json`
- `artifacts/level3_filters/*/filter_scores.jsonl`

