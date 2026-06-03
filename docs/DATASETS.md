# Datasets

## Default Offline Dataset

Quick mode uses the checked-in Tiny Shakespeare mirror at
`data/tinyshakespeare/input.txt`. The loader validates SHA-256 before use. This
keeps CI offline and prevents an implicit large download.

## Configured Adapters

| Config | Provider | Default behavior |
| --- | --- | --- |
| `configs/datasets/tiny_shakespeare.yaml` | Local file | Used by quick mode |
| `configs/datasets/wikitext2.yaml` | Optional Hugging Face stream | Falls back to Tiny Shakespeare offline |
| `configs/datasets/openwebtext_sample.yaml` | Optional Hugging Face stream | Falls back to Tiny Shakespeare offline |
| `configs/datasets/c4_sample.yaml` | Optional Hugging Face stream | Falls back to Tiny Shakespeare offline |
| `configs/datasets/mixed_debug.yaml` | Local debug file | Used for pipeline debugging |

Network access is explicit: call `load_configured_dataset(...,
allow_network=True)`, or run `python scripts/run_dataset_matrix.py --mode full
--allow-network`, and install the optional `datasets` package. Without network
or that package, optional Hugging Face configs fall back to the local Tiny
Shakespeare corpus and mark `used_fallback=true` in the matrix summary.

## Dataset Cards

Each experiment generates `dataset_card.json` with source, usage note, split,
raw and retained characters, retention rate, duplicate removals, PII-like hit
counts, seed, timestamp, and code version when available.

The matrix runner writes per-dataset artifacts to
`artifacts/dataset_matrix/<dataset_name>/` and writes aggregate summaries to
`artifacts/dataset_matrix/dataset_matrix_summary.csv` and
`artifacts/dataset_matrix/dataset_matrix_summary.md`.
