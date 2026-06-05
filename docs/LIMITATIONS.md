# Limitations

- These limitations follow `docs/REPORTING_CONTRACT.md`.
- The primary `main_results` evidence remains WikiText-2 only; 3B
  cross-dataset evidence is reported separately.
- The completed candidate matrix uses the `small` model only.
- The main benchmark uses 3 seeds, so model comparisons are preliminary.
- OpenWebText and C4 English are completed only as real HuggingFace streaming
  samples, not as complete upstream corpora.
- Medium and larger model scales are not completed for the current candidate matrix.
- HDQS++ v1/v2/v3 do not have supported improvement over raw.
- The dev split is used for candidate comparison; held-out test evaluation should
  only be run after method settings are frozen.
- Synthetic privacy and quality diagnostics are useful checks, not formal
  external audits.
- Cross-dataset perplexity should be interpreted within dataset/tokenizer
  boundaries unless tokenizer hash, vocabulary size, parameter count, and token
  budget match.

The project should be presented as an audit benchmark and reproducibility
framework, not as a final method-improvement result.
