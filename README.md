# DataAudit-LM

DataAudit-LM is a reproducible research artifact for auditing
language-model pretraining data filters under controlled token budgets.

It studies a deliberately narrow question: when data source, tokenizer,
model shape, seed, optimizer, and token budget are controlled, do filtering
methods actually improve small decoder-LM utility, or do they mostly expose
tradeoffs such as proxy-utility mismatch, over-filtering, and domain shift?

The project does **not** claim a completed publication benchmark, competition
placement, institutional coursework, or a universal method win over raw data.

## Current Evidence

The current evidence is retained as legacy controlled evidence while the
DataAudit-LM mainline is being migrated into a cleaner implementation path.

- Datasets: `2`
- Source scale: `200006900` GPT-2-token source corpus evidence
- Filtering methods represented in legacy evidence: `7`
- Seeds represented in legacy evidence: `3`
- Historical controlled training runs: `42`
- Tokens per completed historical run: `5001216`
- Aggregate tokens seen: `210051072`
- Small decoder model parameters: `20542752`

The 42 historical controlled runs are useful audit evidence, but they do not
automatically satisfy the new fair DataAudit-LM protocol. They must remain
separated from future frozen-protocol main results.

## Planned Protocol

Planned final matrix:

```text
2 datasets x 6-8 independent methods x at least 5 seeds
```

The final method count depends on whether each method is independently
implemented, non-redundant, and produces a complete decision manifest. A
null-effect control is not counted as an independent effective method, and the
project will not add redundant methods merely to hit a round number.

## What Is Being Migrated

The active package is `src/dataaudit_lm/`. It is replacing wrapper-only access
to old artifacts with tested modules for:

- raw ingestion that retains true duplicate records;
- cluster-aware deterministic splitting;
- exact and near duplicate filtering;
- token-matched random controls;
- reference-LM document scoring;
- selector experiments with documented hypotheses;
- seed-shared initialization and corpus-wide training sampling;
- token-weighted language-model metrics;
- target-only local downstream scoring;
- bootstrap, paired comparison, multiple-testing, and effect-size utilities.

Legacy artifacts remain available for lineage and auditability. They are not
renamed into new final results.

URD-Selector is implemented as a smoke-verified selector pipeline in legacy
artifacts, but it is not yet effectiveness-verified or current main evidence.

## Quick Start

```bash
python -m pytest -q
python scripts/dataaudit_lm/finalize_release.py --audit-only
python scripts/dataaudit_lm/verify_artifacts.py
python scripts/dataaudit_lm/verify_document_consistency.py
```

The grouped wrapper can be run with:

```bash
python scripts/run_all_checks.py --timeout 300
```

## Release Boundary

`python scripts/dataaudit_lm/finalize_release.py --audit-only` writes the
current audit report and may return success while
`final_release_gate_passed=false`.

`python scripts/dataaudit_lm/finalize_release.py --release` is stricter. It
must return a non-zero exit code unless every release gate is satisfied.

## Documentation

- `docs/PROJECT_OVERVIEW.md`: current DataAudit-LM overview
- `docs/EVIDENCE_SCOPE.md`: current evidence scope and boundaries
- `docs/RESULTS.md`: artifact-referenced result summary
- `docs/MIGRATION_MAP.md`: old-to-new implementation migration status
- `docs/STATISTICAL_PROTOCOL.md`: frozen statistical analysis plan
- `docs/DATAAUDIT_SELECTOR_HYPOTHESIS.md`: selector hypothesis and failure modes

## Usage Note

This repository can be discussed as a personal research engineering project,
provided the evidence boundary above is preserved. Do not present it as an
official course submission, a competition result, or a completed full-scale
publication benchmark.
