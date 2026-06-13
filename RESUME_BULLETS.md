# Resume Bullets

- Built a top-tier CCF-C candidate LLM data-quality research artifact over OpenWebText and C4 samples, with 2 real non-fallback corpora, 7 filtering methods, 3 seeds, and 42 controlled small-decoder-LM training runs.
- Scaled the local benchmark to 200M GPT-2-token source data and 210M training tokens_seen, using a 20.5M-parameter decoder LM, GPT-2 tokenizer, fixed context length, per-run manifests, and finite-metric audit checks.
- Compared raw, exact dedup, length filtering, random same-keep-rate, C4-style quality filtering, perplexity-proxy filtering, and URD-fixed under matched training budgets, with per-seed NLL/PPL tables and risk/diversity/cost analysis.
- Added claim-hygiene guardrails so the project can be presented honestly as a strong research prototype without overstating it as an accepted paper, official competition result, or completed Level 3 benchmark.
- Earlier LocalMax V1 release: built a reproducible benchmark over two 20M-token corpora with 24 strengthened small-model training runs and claim hygiene safeguards.
- Built a reproducible 200M-token LLM data-quality auditing benchmark over OpenWebText and C4, comparing raw, exact dedup, length filtering, and URD-fixed across 24 controlled small-model training runs.
- Implemented GPT-2-tokenized data manifests, no-fallback verification, ID-based filtering artifacts, per-token NLL/PPL audit tests, bootstrap confidence intervals, mechanism analysis, and release-bundle integrity checks.
- Preserved honest claim boundaries: reports local evidence only and avoids unsupported publication-readiness, leaderboard, or URD-superiority wording.
