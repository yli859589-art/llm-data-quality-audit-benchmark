# P0-2 Core Correctness Verification

## Data status

Searched the project workspace for the declared LocalMax V2 C4 and OpenWebText
training shards. The nine declared corpus shards remain absent: C4 has 0/3 and
OpenWebText has 0/6. Existing `selected_doc_ids.jsonl.gz` and decision files
are filter metadata, not corpus recovery. No download was started and no
fixture data was used as formal data.

## Implemented corrections

1. `training_v2.sampling.build_document_token_pool` performs a first streaming
   pass over the whole selected training split, ranks IDs with stable SHA-256
   seed priorities, then re-streams only the selected documents. It holds no
   corpus text in the first pass and emits sampling seed, source-pool token
   count, selected IDs, coverage, unique available tokens and budget.
2. LocalMax V2 and CCFC training now use that full-pool sampler rather than
   the old first-file-prefix training loader. New training manifests record
   sampling strategy/seed/pool size; metrics distinguish training tokens,
   unique available training tokens and repeated sampled tokens. CCFC V2 warm
   starts are explicitly `weights_only_initialization`: prior tokens and steps
   are no longer credited as resumed progress.
   Any newly executed P0-2 filters/trainings write below `artifacts/p0_02/`,
   not historical LocalMax output directories.
3. `training_v2.checkpoint` now provides versioned full state checkpoints with
   model, optimizer, optional scheduler, Python/Torch/CUDA RNG state, sampler
   state, step, tokens, configs and data identity. Legacy files return
   `weights_only_initialization`, never `exact_resume`.
4. CCFC random control defaults to `token_budget` matching and writes an audit
   with target, actual, delta, tolerance and indivisible-document caveat.
5. CCFC filter reports now distinguish `documents_scored` proxy from elapsed
   seconds, document/token throughput, Python allocation peak and unavailable
   GPU memory.
6. Cloze scoring masks prompt labels and computes NLL only for target tokens.
   CCFC statistical result claims are disabled for fewer than five independent
   seeds and label unadjusted multi-method results as exploratory only.

## Verification boundary

The new sampler, full-state checkpoint round trip, legacy checkpoint labeling,
token-matched random control and target-only cloze behavior are unit-tested on
temporary CPU fixtures. They are not a claim that the 200M-token historical
matrix was rerun. Full-corpus filter/training/evaluation remains blocked until
the nine declared shard files are restored and hash-verified.

The historical `evaluation_step7/downstream_protocol` hash mismatch is retained
as an original-artifact defect; it was not rewritten to make its test pass.
Existing broad tests that generate reports must run in a disposable worktree or
temporary artifact root. P0-2 did not rerun those writer tests against history.

## P1-1 handoff

After data restoration, replace the in-memory selected-token training buffer
with a resumable shard index/window sampler for multi-epoch streaming at larger
scales. Add near-duplicate split scanning and perform a newly-versioned full
matrix run; do not mix those outputs with historical LocalMax tables.
