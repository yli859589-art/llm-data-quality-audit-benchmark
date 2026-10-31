# P0-1 Baseline and Preflight Audit

## Baseline evidence

This source bundle was not a Git repository at the start of P0-1. Therefore
the requested upstream commit `16b33e8e6fc97be1c0f3475abb23ea8ced9571c8`
cannot be verified from local Git metadata. This is a confirmed limitation, not
a claim that the commit matched. A local `baseline/source-bundle` commit was
created from the unmodified bundle, then work continued on
`upgrade/p0-01-baseline-preflight`; no remote push was performed.

The preflight wrote SHA-256 values for 2,204 existing historical metadata and
result files to `artifacts/upgrade_reports/p0-01_preflight/`. That directory is
ignored so generated reports cannot pollute historical results. Re-run with the
baseline manifest to detect an altered or missing protected file.

## Verified workspace status

| Item | C4 English V2 | OpenWebText V2 |
| --- | ---: | ---: |
| Manifest parses | yes | yes |
| Declared documents | 209,481 | 88,600 |
| Declared GPT-2 tokens | 100,002,807 | 100,004,093 |
| Declared source | `allenai/c4` / `en` | `Skylion007/openwebtext` |
| Internal manifest totals agree | yes | yes |
| Actual declared shards in this checkout | **0 / 3** | **0 / 6** |
| Local shard SHA-256 verification | unavailable | unavailable |

The manifests and declared hash sidecars exist, but the actual real-corpus
shards do not. A manifest is not proof of local data availability. Restore the
exact shards at their declared paths, or re-acquire from the declared sources
while recording source version, cost, disk use, and hashes. P0-1 did not start
large downloads or substitute any fixture/synthetic corpus.

The inspected host has Python 3.12.5, PyTorch 2.11.0+cu126, NumPy, Datasets,
Transformers, PyYAML, and pytest available; CUDA is available. CPU fallback is
supported by the preflight's device check and unit-tested using only temporary
test fixtures, never project data.

## Executed verification

| Command | Actual result |
| --- | --- |
| `python -m pytest tests/test_preflight_project.py -q` | **5 passed** |
| `python scripts/preflight_project.py --mode metadata ...` | **exit 0**; 16 checks, 4 missing-shard/hash warnings |
| `python scripts/preflight_project.py --mode full ...` | **exit 1 (expected)**; 16 checks, 4 failures caused by the 9 missing declared real shards |
| `python -m pytest -q --maxfail=1` | **52 passed, 1 failed**; stopped by `artifacts/evaluation_step7/downstream_protocol/evaluation_manifest.json`, whose `metrics_hash` does not match its referenced metrics file |

The final failure is a pre-existing historical-artifact integrity defect found
during P0-1. It was not repaired because repairing it would alter old evidence;
the baseline hash snapshot was unchanged before and after the check. The full
suite was intentionally stopped at its first failure, so its unexecuted tests
are not reported as passing.

## Architecture and integration observations

| Area | Actual role | Finding |
| --- | --- | --- |
| `src/data*`, `src/tokenization` | sources, splitting, manifests, tokenizers | general pipeline |
| `src/filters_v2`, `src/training_v2`, `src/evaluation_v2` | reusable filters, LM training and evaluation | overlaps with LocalMax scripts |
| `scripts/localmax_v2` | V2 data → filters → training → evaluation/release | linked through V2 artifact manifests |
| `scripts/localmax_ccfc` | CCFC filters → training → evaluation/downstream → artifact checks | linked through `ccfc_utils.py` |

The general modules and LocalMax-specific loops overlap. This is a confirmed
maintenance risk but not, by itself, a confirmed behavioural error; P0-1 does
not merge them before the experiment safety work is complete.

## P0 findings reserved for later stages

1. **Confirmed: file-order training truncation.** Both LocalMax training
   scripts use `_encode_until` in shard/document order. The V2 cap is 1,200,000
   tokens and CCFC is 5,500,000, so selected IDs do not ensure coverage of the
   complete filtered pool. P0-2 should add deterministic full-pool sampling,
   coverage manifests, and token-budget tests.
2. **Confirmed: incomplete resume.** V2 and CCFC checkpoints save/load model
   weights but not optimizer/scheduler state, random states, dataloader position
   or exact progress. P0-3 needs a versioned resume format and interrupted vs
   uninterrupted equivalence test.
3. **Confirmed: random control matches document count, not tokens.** CCFC
   `random_same_keep_rate` selects the number of documents retained by the
   length filter. P0-4 needs token matching with a persisted tolerance audit.
4. **Confirmed risk: weak inference with three seeds.** Both V2 and CCFC
   bootstrap three paired differences and permit a positive conclusion from a
   positive interval without multiplicity handling. P0-4 must define an
   estimand, minimum seeds and decision rule.
5. **Confirmed: cloze loss includes prompts.** CCFC downstream sends
   `prompt + target` as the LM labels, hence prompt loss contributes. P0-5 must
   mask prompts and add a hand-computable regression test.
6. **Confirmed limitation: cost is a document-count proxy.** Filter output uses
   `filter_cost_units=len(decisions)` / `documents_scored`; it is not wall time,
   memory, FLOPs or energy. P0-5 should record measured costs.
7. **Unverified: net exact-dedup effect.** Manifests claim zero output duplicates
   after preparation, then filters deduplicate again. Missing shards prevent
   measurement of duplicates surviving the first pass. P0-2 must report
   before/after counts on recovered real data.

## P0-2 handoff

Change scope: `scripts/localmax_v2/run_localmax_v2_training.py`,
`scripts/localmax_ccfc/run_ccfc_training.py`, their training configurations and
new deterministic sampling tests. Prerequisites: recover/hash-verify all nine
real shards and preserve this baseline. Acceptance: each method uses the same
declared token budget from the full selected pool, records seed/order/coverage,
and proves no file-order truncation by regression test.
