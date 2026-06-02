# Ethics

The default experiment injects synthetic PII-like canaries into public-domain
debug text. It does not require private personal data. Reports redact removed
examples before writing them to disk.

For larger dataset experiments:

1. Review the upstream dataset card, terms, and redistribution policy.
2. Avoid publishing raw documents or recovered PII.
3. Treat filtering scores as engineering heuristics, not labels of author or
   community quality.
4. Measure language and domain bias before deploying any filter beyond a
   research prototype.
5. Disclose AI assistance and follow the target course or venue policy.
