# Limitations

- Quick results are single-seed or small-seed CPU smoke-test evidence.
- Tiny Shakespeare, `mixed_debug`, `synthetic_web_noise`, and
  `local_wikitext_sample` are compact debugging or prototype corpora, not
  production web crawls.
- Paper-prototype optional public rows are fallback records unless approved
  network access or local dataset files are provided.
- Controlled corruption is useful for reproducible stress testing but does not
  estimate natural web-noise rates.
- HDQS++ weights are not tuned on a held-out development split in quick mode.
- Standalone HDQS can be weaker than the raw baseline in quick runs; the
  current evidence supports evaluating the full pipeline rather than HDQS
  alone.
- Current three-seed comparisons have favorable mean directions for several
  candidates, but wide confidence intervals prevent paper-level claims.
- BPE and larger model configs are present as research-system scaffolding, but
  default quick artifacts train only compact character models.
- Synthetic-canary checks are not formal privacy certification,
  membership-inference testing, or a guarantee that real private data is safe.
- CPU attention timing is hardware-dependent; SDPA is an optimized PyTorch
  primitive, not a new algorithmic contribution.
- The project is not official coursework, not a competition result, not a
  submitted paper, and not an accepted paper.
