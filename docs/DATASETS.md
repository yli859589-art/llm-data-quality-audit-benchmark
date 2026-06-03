# Datasets

## Configured Matrix

Dataset configs live under `configs/datasets/`:

- `tiny_shakespeare`: local, checksum-verified public debugging corpus.
- `mixed_debug`: local Tiny Shakespeare-backed debug entry for mixed-noise
  matrix checks.
- `synthetic_web_noise`: local pseudo-real web-noise sample for deterministic
  stress tests.
- `local_wikitext_sample`: local WikiText-style sample for offline
  paper-prototype validation.
- `wikitext2`: optional streamed WikiText-2 adapter.
- `openwebtext_sample`: optional streamed OpenWebText sample adapter.
- `c4_sample`: optional streamed C4 sample adapter.

Optional public datasets require explicit network permission and upstream
dataset-card review. Offline mode falls back to Tiny Shakespeare and records
`used_fallback=true`.

## Modes

- `quick`: `tiny_shakespeare`, `mixed_debug`.
- `paper-prototype`: four local entries are trained in lightweight small-run
  mode; optional remote entries record fallback unless local files or approved
  network access are available. Dry-run support remains available for routing
  checks.
- `full`: all configured entries with longer training and optional network.

Every dataset-matrix entry writes a relative output path and a
`dataset_card.json`. Paper-prototype entries also write `results.json` and
`fallback_report.json`. Dry-run cards record source, license note, fallback
status, and `dry_run=true`; trained cards include raw/retained characters,
retention rate, number of documents, seed, token budget, variants run, runtime,
and command.
