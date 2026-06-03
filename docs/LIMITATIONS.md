# Limitations

- Quick artifacts are single-seed CPU smoke-test evidence.
- Tiny Shakespeare is a compact debugging corpus, not a production web crawl.
- Controlled corruption makes comparisons reproducible but does not estimate
  natural web-corpus noise rates.
- HDQS is transparent and testable, but its weights need tuning on a separate
  development set before a paper-style claim.
- In the current quick stress test, standalone HDQS filtering is not a stable
  improvement over the raw noisy baseline; the stronger preliminary result is
  the full pipeline that combines cleaning, redaction, deduplication, and HDQS.
- Character-level MiniGPT results do not establish scaling behavior for modern
  tokenized LLMs.
- Synthetic-canary checks validate redaction behavior; they are not a formal
  privacy audit, membership-inference evaluation, or memorization study.
- CPU attention memory values are algorithmic estimates. Actual CUDA peak
  allocation is reported only when CUDA runs are performed.
- Optional public-dataset adapters require explicit network access and an
  upstream license or usage review.
- Strict lint/type checking is enforced first for the main LLM benchmark
  modules. Legacy supporting modules are kept functional and covered by smoke
  tests, with stricter typing planned as future work.
