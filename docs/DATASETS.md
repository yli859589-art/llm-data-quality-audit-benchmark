# Datasets

## Configured Matrix

Dataset configs live under `configs/datasets/`:

- `tiny_shakespeare`: local, checksum-verified public debugging corpus.
- `mixed_debug`: local Tiny Shakespeare-backed debug entry for mixed-noise
  matrix checks.
- `wikitext2`: optional streamed WikiText-2 adapter.
- `openwebtext_sample`: optional streamed OpenWebText sample adapter.
- `c4_sample`: optional streamed C4 sample adapter.

Optional public datasets require explicit network permission and upstream
dataset-card review. Offline mode falls back to Tiny Shakespeare and records
`used_fallback=true`.

## Modes

- `quick`: `tiny_shakespeare`, `mixed_debug`.
- `paper-prototype`: all configured entries with offline fallback and dry-run
  support.
- `full`: all configured entries with longer training and optional network.

Every dataset-matrix entry writes a relative output path and a
`dataset_card.json`. Dry-run cards record source, license note, fallback
status, and `dry_run=true`; trained cards include data-processing metrics.
