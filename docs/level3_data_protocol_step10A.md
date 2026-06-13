# Level 3 Data Protocol Step 10A

The Level 3 data protocol requires at least three real, no-fallback corpora with
tokenizer-specific BPE token counts.

## Required Minimum

- Required datasets: `openwebtext`, `c4_en`, and `fineweb`.
- Optional extension: `dolma_or_pile`.
- Minimum floor: 500M BPE tokens per required dataset.
- Strong target: 1B BPE tokens per dataset when compute allows.
- Required evidence: source note, license-scope note, split hashes, document
  count, BPE token count, no-fallback flag, and split-integrity status.

## Step 10A Boundary

No heavy dataset is prepared in Step 10A. Existing streaming samples remain
bounded audit evidence and cannot satisfy the Level 3 data gate.

## Future Artifacts

- `artifacts/level3_data/*/data_manifest.json`
- `artifacts/level3_data/*/split_integrity.json`
- `artifacts/level3_data/*/license_scope.md`

