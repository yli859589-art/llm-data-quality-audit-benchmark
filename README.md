# DataAudit-LM

**A reproducible multi-dataset benchmark for auditing LLM pretraining-data filters under controlled training budgets.**

DataAudit-LM evaluates independent filtering strategies on 100M-token samples
from OpenWebText and C4 using controlled multi-seed decoder-language-model
training. The repository includes deterministic data manifests, filter
decisions, training lineage, per-token language-model evaluation, statistical
comparisons, downstream probes, checkpoint integrity checks, and reproducible
release tooling.

## Research Question

Do pretraining-data filters improve language-model utility under matched token
budgets, and when do simple baselines behave more reliably than compound
quality selectors?

## Core Features

- Real non-fallback OpenWebText and C4 samples.
- Deterministic filter outputs and per-run training lineage.
- Controlled small decoder-language-model training with GPT-2 tokenization.
- Per-token NLL, log-PPL, and PPL audit checks without clipping.
- Risk, diversity, cost, stability, and local downstream probe artifacts.
- Explicit evidence boundaries for incomplete or mixed findings.

## Evidence Summary

| Item | Current value |
|---|---:|
| Source datasets | 2 |
| Source GPT-2 tokens | 200006900 |
| Filtering methods | 7 |
| Seeds | 3 |
| Completed training runs | 42 |
| Target training runs for the frozen expanded matrix | 80 |
| Tokens per completed run | 5001216 |
| Aggregate tokens seen | 210051072 |
| Model parameters | 20542752 |
| Local downstream probe rows | 8 |

The current reusable evidence is a completed 42-run controlled matrix. It is
not described as the frozen expanded 80-run matrix because that larger gate has
not been executed.

## Main Findings

Filtering effects are dataset-dependent. No method is described as universally
superior unless it is supported across datasets, seeds, corrected statistical
tests, and downstream evaluations. Current evidence should be read as an audit
of filtering behavior under local compute constraints, with mixed and negative
findings preserved.

## Benchmark Design

DataAudit-LM separates data ingestion, filtering, training, evaluation,
statistics, and release integrity checks. Large raw shards and model
checkpoints are kept out of ordinary Git history; manifests, hashes, metrics,
tables, and lightweight reports remain in the repository.

## Repository Structure

```text
src/dataaudit_lm/          Public package namespace
scripts/dataaudit_lm/      Verification and release entrypoints
configs/                   Experiment and protocol configuration
docs/                      Project documentation
artifacts/dataaudit_lm/    Public release reports, tables, and integrity files
tests/                     Automated tests
```

## Installation

```bash
python -m pip install -e .
python -m pip install -r requirements-dev.txt
```

## Quick Verification

```bash
python scripts/dataaudit_lm/audit_metric_correctness.py
python scripts/dataaudit_lm/audit_experiment_fairness.py
python scripts/dataaudit_lm/verify_artifacts.py
python scripts/dataaudit_lm/finalize_release.py
python -m pytest tests/test_dataaudit_lm_phase1.py -q
```

## Full Experiment Reproduction

The repository keeps executable pipelines for data preparation, filtering,
training, evaluation, and statistical analysis. Full retraining is intentionally
separate from quick verification because it requires GPU time and large local
artifacts.

## Results

Canonical public summaries are generated from machine-readable artifacts by:

```bash
python scripts/dataaudit_lm/finalize_release.py
```

The generated report is:

```text
artifacts/dataaudit_lm/reports/final_release_report.json
```

## Data Provenance

The current data evidence uses OpenWebText and C4 English samples with GPT-2
token accounting. Large source shards are not committed to ordinary Git
history. Use the local release bundle or rerun the data preparation scripts to
recreate large artifacts.

## Limitations

- The current reusable matrix has 42 completed runs, not 80.
- The local downstream probe is diagnostic and is not a replacement for a full
  external task suite.
- Some legacy directories remain during the migration and are not part of the
  cleaned public package namespace.
- The reference-model filtering path and raw duplicate-retention policy require
  another audit before stronger method conclusions are made.

## Citation

If you use this repository, cite it as the DataAudit-LM reproducible benchmark
for LLM pretraining-data filtering.

## License

This project is released under the license in `LICENSE`.
