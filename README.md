# LLM Data Quality Evaluation and Intelligent Filtering System

> Audited source release of a research prototype for language-model data-quality diagnosis, filtering, scalable processing, and reproducible training checks.

## Scope

This repository publishes the final audited source snapshot from `audit/final-independent-verification` (source commit `c491337`, a descendant of audit fix `fe97f5f`). It includes the P0-1, P0-2, P1-1, P1-2, P2-1 and P2-2 upgrades, plus the independent-audit documentation.

Included components:

- Unified `quality_system` service and command-line interface.
- Streamlit UI at `apps/quality_system_app.py`.
- Scalable JSONL/GZIP pipeline with resumable state and shard-level processing.
- Persistent MinHash/LSH deduplication with exact Jaccard confirmation.
- Deterministic checkpoint/resume utilities for the training path.
- Tests, configuration, CI configuration, installation material, and final audit records.

This is a source-and-documentation release. It intentionally excludes raw C4/OpenWebText corpora, large filter outputs, model checkpoints, caches, and ZIP deliverables. See [docs/GITHUB_PUBLICATION_NOTES.md](docs/GITHUB_PUBLICATION_NOTES.md) for the exact boundary.

## Installation

Python 3.10 or later is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[data,tokenizers,ui,dev]"
```

For a minimal non-UI install, use `python -m pip install -e ".[data,tokenizers]"`.

## Run the system

```powershell
python scripts/quality_system.py --help
python scripts/quality_system.py check C:\data\sample.jsonl
python scripts/quality_system.py import demo C:\data\sample.jsonl --source local
python scripts/quality_system.py analyze demo --sample-limit 10000
python scripts/quality_system.py run demo raw --task-id demo-raw
python scripts/quality_system.py status demo-raw
python scripts/quality_system.py export demo-raw
streamlit run apps/quality_system_app.py --server.address 127.0.0.1
```

Additional examples are in [docs/FINAL_INSTALLATION_GUIDE.md](docs/FINAL_INSTALLATION_GUIDE.md) and [docs/P2_01_SYSTEM.md](docs/P2_01_SYSTEM.md).

## Validation status and limitations

- The independently audited P0-P2 software paths passed their targeted checks.
- The isolated full historical suite was **313 passed, 3 failed**. This release does **not** claim that all `pytest` tests pass; the three failures are confined to an older frozen LocalMax release-regeneration subsystem.
- None of the declared official corpus shards are present: C4 is **0/3** and OpenWebText is **0/6**. Full real-corpus experiments, real PPL, and formal effectiveness claims are therefore **blocked** and incomplete.
- Twenty historical manifest/hash anomalies remain documented as strict legacy integrity exceptions; they are not silently reclassified as successes.
- The CLI/service fixture integration path is tested. A fresh complete manual click-through of all six Streamlit pages was not rerun in the final independent audit, so it must not be inferred from backend checks.

Read [docs/FINAL_INDEPENDENT_AUDIT.md](docs/FINAL_INDEPENDENT_AUDIT.md), [docs/FINAL_DEFECT_REGISTER.md](docs/FINAL_DEFECT_REGISTER.md), and [docs/FINAL_RELEASE_VERIFICATION.md](docs/FINAL_RELEASE_VERIFICATION.md) before using results or making research claims.

## Test commands

```powershell
python -m pytest -q
python scripts/run_all_checks.py --timeout 300
```

The first command reproduces the known historical LocalMax limitations above; do not remove or hide those failures to represent the project as fully passing.

## License and research-use note

See [LICENSE](LICENSE). This project is a personal research/portfolio prototype, not a completed cloud-scale benchmark or a claim of a data-filtering method win.
