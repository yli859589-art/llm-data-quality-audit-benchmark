# Limitations

- Quick results are smoke-test evidence for reproducibility and
  instrumentation, not paper-level model-quality evidence.
- Paper-prototype results are lightweight small runs. They show that the
  experiment matrix is executable, not that the method is proven at scale.
- Tiny Shakespeare, `mixed_debug`, `synthetic_web_noise`, and
  `local_wikitext_sample` are compact debugging or prototype corpora, not
  production web crawls.
- Optional public dataset entries are fallback records unless approved local
  files or approved network access are provided.
- Controlled and pseudo-real noise families are deterministic stress tests;
  they do not estimate natural web-noise prevalence.
- HDQS++ weights are not tuned and frozen on a held-out development split.
- DQCS curriculum artifacts are diagnostics and do not yet prove stable
  curriculum-training gains.
- Current multi-seed comparisons have wide confidence intervals.
- BPE and larger model configs are represented in model-scaling artifacts, but
  not all listed configs are trained in quick or CI mode.
- Synthetic-canary privacy checks are not formal privacy certification,
  membership-inference testing, or a guarantee for real private data.
- Downstream metrics are lightweight proxies and should be expanded before
  paper submission.
- CPU/CUDA attention timings are hardware-dependent and are auxiliary systems
  checks.
- The project is not official coursework, not a competition result, not a
  submitted paper, and not an accepted paper.
