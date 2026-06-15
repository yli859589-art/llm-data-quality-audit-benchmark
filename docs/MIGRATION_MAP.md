# DataAudit-LM Migration Map

This map separates reusable legacy assets from the new DataAudit-LM mainline.
Adapter-only code that merely reads old artifacts is not marked as migrated.

| Module | Legacy path | Canonical new path | Status | Runtime dependency | Artifact dependency | Planned removal stage |
|---|---|---|---|---|---|---|
| Data loading | `scripts/localmax*`, `src/data_sources` | `src/dataaudit_lm/data` | `VALIDATED` | new package | rehearsal manifest | after frozen protocol |
| Tokenizer | `src/tokenization` | future `src/dataaudit_lm/tokenization` | `ADAPTER_ONLY` | legacy config | historical manifests | after tokenizer freeze |
| Dataset manifest | `src/data_sources/manifest.py` | `src/dataaudit_lm/data/manifests.py` | `MIGRATED` | new package | rehearsal manifest | keep both until final matrix |
| Filtering methods | `src/filters_v2`, `scripts/localmax*` | `src/dataaudit_lm/filters` | `VALIDATED` | new package | rehearsal manifests | after parity audit |
| Model definition | `src/models_v2` | `src/dataaudit_lm/models` | `MIGRATED` | new package | rehearsal checkpoint | after training parity |
| Training loop | `src/training_v2`, localmax scripts | `src/dataaudit_lm/training` | `MIGRATED` | new package | rehearsal training manifests | after full rehearsal |
| Checkpoint | localmax artifacts | `src/dataaudit_lm/training/checkpoints.py` | `MIGRATED` | new package | rehearsal checkpoint | keep hashes |
| LM evaluation | `src/evaluation_v2/lm_metrics.py` | `src/dataaudit_lm/evaluation/lm_metrics.py` | `VALIDATED` | new package | metric tests | after metric parity |
| Downstream | `src/evaluation_v2/downstream.py` | `src/dataaudit_lm/evaluation/downstream.py` | `MIGRATED` | new package | rehearsal target-only probe | after official task decision |
| Statistical analysis | `src/evaluation_v2/statistics.py` | `src/dataaudit_lm/statistics` | `MIGRATED` | new package | protocol only | after multi-seed matrix |
| Registry | `artifacts_v2` | `src/dataaudit_lm/registry` | `ADAPTER_ONLY` | legacy artifacts | old reports | after registry v3 |
| Hash/integrity | mixed scripts | `src/dataaudit_lm/integrity` | `VALIDATED` | new package | release reports | keep |
| Figure/table generation | localmax scripts | future `src/dataaudit_lm/reporting` | `NOT_STARTED` | legacy scripts | old tables | after result freeze |
| Release tooling | localmax scripts | `scripts/dataaudit_lm/finalize_release.py` | `MIGRATED` | new package | audit report | after gates pass |

Current rule: 42 historical controlled runs remain legacy evidence. They are
not renamed into new fair-protocol main results.
