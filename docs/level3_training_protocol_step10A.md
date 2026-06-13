# Level 3 Training Protocol Step 10A

The training protocol specifies future small, medium, and selected large-lite
evidence. It does not run training in Step 10A.

## Minimum Model Matrix

- `small`: required for primary datasets and major methods.
- `medium`: required for Level 3 evidence.
- `large_lite`: selected exploratory runs are required for stronger evidence.
- `tiny_smoke`: pipeline check only, not Level 3 evidence.

## Seed and Manifest Rules

- Main small/medium runs require at least seeds `13`, `42`, and `101`.
- Training manifests must record tokens seen, dataset lineage, tokenizer lineage,
  checkpoint lineage, runtime cost metadata, and failure state when applicable.
- Checkpoint manifests are required for completed future training runs.

## Boundary

Step 10A forbids training execution, completed training manifests, and new PPL
result writing.

