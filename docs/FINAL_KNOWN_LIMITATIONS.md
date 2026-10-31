# Final known limitations

- **BLOCKED_BY_MISSING_DATA:** 0/3 declared C4 and 0/6 declared OpenWebText
  shards are present.  The 2×100M-token scale, real-corpus filtering outcomes,
  cross-dataset leakage, and full model experiments are therefore not accepted.
- Seven historical Step 7 evaluation manifests have stale referenced hashes,
  including the downstream-protocol metrics/report pair.  Their source evidence
  is intentionally immutable; the checker reports explicit read-only legacy
  exceptions instead of treating those manifests as valid current evidence.
- Raw is resumable/streaming in the unified system.  Batch-dependent filters
  retain their bounded input cap because forcing a prefix-wise implementation
  would alter global deduplication or ranking semantics.
- The random baseline exposed by the generic system is same-document-rate
  control.  It does not claim exact token matching outside the specialised
  legacy CCFC configuration.
- Streamlit and browser operation are verified on Windows only.  Linux and
  full-scale GPU/real-corpus validation are NOT_RUN.
