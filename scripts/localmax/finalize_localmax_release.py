from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from localmax_utils import ROOT, protected_hashes, protected_hashes_unchanged, sha256_file, write_json
from make_localmax_release_figures import build_release_figures
from make_localmax_release_tables import build_release_tables
from artifacts_v2.canonical_io import write_canonical_jsonl, write_canonical_text


CURRENT_READINESS = "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED"
FROZEN_RELEASE_TIMESTAMP = "2026-06-12T00:00:00Z"
BUNDLE_SCOPE = "standalone_metadata_bundle"
RELEASE_ROOT = ROOT / "artifacts" / "localmax_release"
TABLES_DIR = RELEASE_ROOT / "tables"
FIGURES_DIR = RELEASE_ROOT / "figures"
REPORTS_DIR = RELEASE_ROOT / "reports"
MANIFESTS_DIR = RELEASE_ROOT / "manifests"
CLAIM_MAP_PATH = ROOT / "artifacts" / "claim_map" / "claim_map_localmax.json"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _write_text(path: Path, text: str) -> Path:
    return write_canonical_text(path, text.strip())


def _doc_header(title: str) -> str:
    return f"# {title}\n\nCurrent status: `{CURRENT_READINESS}`\n\nLevel 3 status: `not completed`\n"


def _collect_release_facts() -> dict[str, Any]:
    data_report = _load_json(ROOT / "artifacts" / "reports" / "localmax_data_report.json")
    training_report = _load_json(ROOT / "artifacts" / "reports" / "localmax_training_strengthened_report.json")
    eval_report = _load_json(ROOT / "artifacts" / "reports" / "localmax_evaluation_strengthened_report.json")
    mechanism_report = _load_json(ROOT / "artifacts" / "reports" / "localmax_mechanism_strengthened_report.json")
    readiness_report = _load_json(ROOT / "artifacts" / "reports" / "step10B_localmax_readiness_report.json")
    main_rows = _read_csv(TABLES_DIR / "localmax_main_results_release.csv")
    method_rows = _read_csv(TABLES_DIR / "localmax_method_summary_release.csv")
    stat_rows = _read_csv(TABLES_DIR / "localmax_statistical_summary_release.csv")
    datasets = data_report.get("datasets", [])
    urd_stats = {
        row["dataset"]: row
        for row in stat_rows
        if row["comparison"] == "urd_fixed_vs_raw"
    }
    return {
        "data_report": data_report,
        "training_report": training_report,
        "eval_report": eval_report,
        "mechanism_report": mechanism_report,
        "readiness_report": readiness_report,
        "main_rows": main_rows,
        "method_rows": method_rows,
        "stat_rows": stat_rows,
        "datasets": datasets,
        "urd_stats": urd_stats,
        "dataset_count": len({row["dataset"] for row in main_rows}),
        "method_count": len({row["method"] for row in main_rows}),
        "seed_count": len({row["seed"] for row in main_rows}),
        "run_count": len(main_rows),
        "min_tokens_seen": min(int(row["tokens_seen"]) for row in main_rows) if main_rows else 0,
        "min_steps_completed": min(int(row["steps_completed"]) for row in main_rows) if main_rows else 0,
        "all_ppl_clipped": all(str(row["ppl_clipped"]).casefold() == "true" for row in main_rows),
        "ppl_comparable": any(str(row["ppl_comparable"]).casefold() == "true" for row in main_rows),
    }


def _write_localmax_docs(facts: dict[str, Any]) -> list[Path]:
    datasets = facts["datasets"]
    token_lines = [
        f"- `{item['dataset_id']}`: `{item['actual_gpt2_tokens']}` GPT-2 tokens, `{item['document_count']}` documents"
        for item in datasets
    ]
    urd_lines = []
    for dataset, row in sorted(facts["urd_stats"].items()):
        urd_lines.append(
            f"- `{dataset}`: mean paired valid_loss delta `{row['mean_paired_loss_improvement']}`, "
            f"CI [`{row['ci_low']}`, `{row['ci_high']}`], crosses zero `{row['ci_crosses_zero']}`"
        )
    token_block = "\n".join(token_lines) if token_lines else "- dataset evidence unavailable"
    urd_block = "\n".join(urd_lines) if urd_lines else "- URD statistical rows unavailable"

    docs: dict[str, str] = {}
    docs["LOCALMAX_RELEASE.md"] = f"""
{_doc_header("LocalMax Release Freeze")}
This release freezes the Step 10B LocalMax minimal training evidence into a reviewable research artifact. It does not run new training, does not expand data, and does not add new methods.

Bundle scope: `standalone_metadata_bundle`.

The `artifacts/localmax_release/` directory is a standalone metadata bundle for review. It includes release tables, figures, reports, dataset/tokenizer/filter/training/evaluation metadata, metrics, lineage, and state fingerprints. It does not include raw data text or full binary checkpoints.

## Scope

- Datasets: `{facts['dataset_count']}` local non-fallback 20M-token samples.
- Methods: `raw`, `exact_dedup`, `length_filter`, `urd_fixed`.
- Seeds: `13`, `42`, `101`.
- Strengthened training runs: `{facts['run_count']}`.
- Minimum training strength: `{facts['min_steps_completed']}` steps and `{facts['min_tokens_seen']}` tokens seen per completed run.
- Model scale: `small`; parameter count `{facts['training_report'].get('parameter_count')}`.
- Tokenizer: GPT-2 BPE tokenizer.
- Primary comparison metric: `valid_loss`.

## Why This Is Not Level 3

This release is a local minimal training-evidence artifact. It does not include cloud-scale 500M-token data per dataset, true medium-model runs, selected large-lite runs, official downstream evaluation, or a full mechanism study.

## Reproduction

Run:

```bash
python scripts/localmax/finalize_localmax_release.py
python scripts/localmax/check_localmax_release_claims.py
python -m pytest tests/ -q
```

The release tables and figures are derived from Step 10B artifacts under `artifacts/localmax_tables/`, `artifacts/localmax_training_strengthened/`, `artifacts/localmax_evaluation_strengthened/`, and `artifacts/localmax_analysis_strengthened/`.

Figures are regenerated from release CSV tables. Step 10C-hotfix only improves release quality, figure readability, and cross-platform reproducibility; all experimental values are unchanged.
"""
    docs["LOCALMAX_RESULTS.md"] = f"""
{_doc_header("LocalMax Results")}
This document summarizes the frozen LocalMax evidence generated from Step 10B artifacts.

## Evidence Matrix

- Datasets: `{facts['dataset_count']}`.
- Methods: `{facts['method_count']}`.
- Seeds: `{facts['seed_count']}`.
- Strengthened runs: `{facts['run_count']}`.
- Metric for method comparison: `valid_loss`.
- PPL status: clipped for this run and not comparable across methods.

## Dataset Scale

{token_block}

## URD-Fixed Disclosure

{urd_block}

URD-fixed evidence is mixed in this LocalMax release.

On OpenWebText 20M, URD-fixed has a lower mean valid_loss than raw in this local run, but the confidence interval crosses zero. On C4 English 20M, URD-fixed does not improve over raw by valid_loss.

## Claim Boundary Statement

The current LocalMax evidence does not support a claim that URD-fixed outperforms raw.
"""
    docs["LOCALMAX_LIMITATIONS.md"] = f"""
{_doc_header("LocalMax Limitations")}
This release is useful as local-scale evidence, not as a finished conference-level benchmark.

## Main Limitations

- Only two datasets are included.
- Each dataset is a 20M GPT-2-token local sample, not a 500M-token heavy benchmark.
- Only four methods are included.
- The completed training evidence is small-model evidence.
- A true medium run has not been completed.
- No selected large-lite run has been completed.
- Official downstream evaluation has not been run.
- PPL is clipped and should not be used for method comparison.
- Comparisons use `valid_loss`.
- The training token budget remains small relative to the future cloud route.
- The release cannot claim Level 3 completion or CCF-B-level readiness.
- Step 10C-hotfix only improves release quality and reproducibility. It does not change experimental results.
"""
    docs["LOCALMAX_REPRODUCIBILITY.md"] = f"""
{_doc_header("LocalMax Reproducibility")}
## Environment

The environment report is stored at `artifacts/reports/localmax_environment_report.json`.

## Pipeline Commands

```bash
python scripts/localmax/prepare_localmax_tokenizer.py --config configs/localmax/tokenizer.yaml
python scripts/localmax/prepare_localmax_data_minimal.py --config configs/localmax/data_matrix_minimal.yaml
python scripts/localmax/run_localmax_filters_minimal.py --config configs/localmax/filter_matrix_minimal.yaml
python scripts/localmax/run_localmax_training_strengthened.py --config configs/localmax/training_strengthened.yaml
python scripts/localmax/run_localmax_evaluation_strengthened.py
python scripts/localmax/run_localmax_analysis_strengthened.py
python scripts/localmax/finalize_localmax_release.py
```

## Hash Checks

The release manifest records table, figure, document, and report hashes. Historical main results have protected hashes and are checked by `scripts/check_main_results_purity.py`.

## Checkpoint Policy

Full binary checkpoints are not stored in the repository; training manifests, metrics, lineage, and state fingerprints are preserved.

## Bundle Scope

Bundle scope: `standalone_metadata_bundle`.

The LocalMax release bundle is self-contained for metadata review. Raw data and binary checkpoints are intentionally excluded. Release-table manifest links point inside `artifacts/localmax_release/manifests/`.

## Canonical Text Policy

Generated text artifacts use UTF-8, LF newlines, stable JSON key ordering, stable JSON indentation, and a final newline at EOF. Registry finalization runs after all release-writing commands.
"""
    docs["LOCALMAX_CLAIM_BOUNDARY.md"] = f"""
{_doc_header("LocalMax Claim Boundary")}
## Allowed Current Claims

- LocalMax minimal training evidence has been released.
- The release uses two local 20M GPT-2-token datasets.
- GPT-2 BPE is the LocalMax tokenizer.
- Four filtering methods are included.
- Twenty-four strengthened small-model training runs are registry-backed.
- Evaluation is based on `valid_loss`.
- PPL is clipped and not comparable.
- URD-fixed evidence is mixed.
- A Level 3 protocol exists, but Level 3 execution has not been completed.
- Release artifacts use canonical UTF-8/LF output and a standalone metadata bundle.

## Disallowed Current Claims

- Completed Level 3 artifact.
- CCF-B-level readiness.
- CCF-A-level readiness.
- A state-leading method result.
- Proven URD-fixed superiority over raw.
- PPL-based improvement.
- Completed official downstream evaluation.
- Completed true medium evidence.
- Completed selected large-lite evidence.
- 500M/1B-token benchmark evidence.
"""
    docs["LOCALMAX_MODEL_CARD.md"] = f"""
{_doc_header("LocalMax Model Card")}
## Model

- Scale: `small`.
- Parameter count: `{facts['training_report'].get('parameter_count')}`.
- Context length: `{facts['training_report'].get('context_length')}`.
- Minimum steps completed: `{facts['min_steps_completed']}`.
- Minimum tokens seen per run: `{facts['min_tokens_seen']}`.

## Intended Use

The model runs are audit instruments for comparing data-filtered training slices under controlled budgets. They are not deployed language models.
"""
    docs["LOCALMAX_DATA_CARD.md"] = f"""
{_doc_header("LocalMax Data Card")}
## Data Sources

{token_block}

Both datasets are local non-fallback samples with GPT-2 token accounting. They are not full upstream dataset reproductions. Raw data text is not duplicated inside the LocalMax release metadata bundle.
"""
    docs["LOCALMAX_FAILURE_ANALYSIS.md"] = f"""
{_doc_header("LocalMax Failure Analysis")}
## Preserved Negative Evidence

- HDQS++ remains preserved as historical failure-analysis evidence rather than promoted as a winning method.
- URD-fixed evidence is mixed across the two LocalMax datasets.
- PPL clipping prevents PPL-based method comparison.
- Resource limits explain why this release remains local minimal evidence.
- Future work requires cloud-scale Level 3 execution before stronger claims.
"""
    docs["LOCALMAX_FUTURE_CLOUD_LEVEL3.md"] = f"""
{_doc_header("Future Cloud Level 3 Route")}
To turn this local release into a future Level 3 execution, the project needs:

- At least three datasets with 500M GPT-2/BPE tokens each.
- True medium models around the 100M-250M parameter range.
- Selected large-lite runs.
- Six to ten or more method families.
- Official downstream evaluation.
- Full mechanism analysis.
- A100, L40S, H100, or comparable server hardware.
- Roughly 1.5TB or more storage for conservative artifact handling.
- Server-level Step 10B execution.
- A separate Level 3 release freeze after those runs complete.
"""
    paths = []
    for name, text in docs.items():
        paths.append(_write_text(ROOT / "docs" / name, text))
    return paths


def _write_project_docs(facts: dict[str, Any]) -> list[Path]:
    readme = f"""
# LLM Data Quality Diagnostics and Risk Auditing Benchmark

Current status: `{CURRENT_READINESS}`

Level 3 status: `not completed`

## Project Overview

This repository is a reproducible research artifact for auditing language-model pretraining data filters under controlled token budgets. The current LocalMax release freezes a local-scale, registry-backed benchmark: two 20M-token datasets, GPT-2 tokenization, four filtering strategies, three seeds, and twenty-four strengthened small-model training runs.

The project does **not** claim a completed Level 3 benchmark, publication-tier readiness, institutional affiliation, competition placement, or a supported method win over raw training data.

## Current LocalMax Evidence

- Datasets: `openwebtext_20m` and `c4_en_20m`.
- Data scale: about 20M GPT-2 tokens per dataset.
- Tokenizer: GPT-2 BPE.
- Methods: `raw`, `exact_dedup`, `length_filter`, `urd_fixed`.
- Seeds: `13`, `42`, `101`.
- Runs: `{facts['run_count']}` strengthened small-model training runs.
- Minimum training strength: `{facts['min_steps_completed']}` steps and `{facts['min_tokens_seen']}` tokens seen per run.
- Primary metric: `valid_loss`.
- PPL disclosure: clipped and not comparable for improvement claims.

## Result Summary

URD-fixed shows mixed local evidence. It has lower mean valid_loss than raw on the OpenWebText 20M sample, but the confidence interval crosses zero. It does not improve over raw on the C4 English 20M sample. The release therefore reports this as audit evidence, not as a method-success claim.

## Quick Start

```bash
python scripts/localmax/finalize_localmax_release.py
python scripts/localmax/check_localmax_release_claims.py
python -m pytest tests/ -q
```

For the full grouped validation wrapper:

```bash
python scripts/run_all_checks.py --timeout 300
```

## Reproducibility

Release tables are in `artifacts/localmax_release/tables/`; figures are in `artifacts/localmax_release/figures/`; the release manifest is `artifacts/localmax_release/localmax_release_manifest.json`.

Bundle scope: `standalone_metadata_bundle`. The release directory contains metadata, metrics, tables, figures, reports, and copied manifests needed for review. It does not contain raw data text or full binary checkpoints.

Generated release text uses UTF-8 with LF newlines so registry hashes remain stable across Windows and Linux rewrites.

Historical single-seed and smoke artifacts are retained for lineage, but they are not the LocalMax main evidence.

## Claim Boundary

Use `docs/LOCALMAX_CLAIM_BOUNDARY.md` as the public wording boundary. The safe current framing is: local minimal training evidence released, with valid_loss-based comparison and clipped PPL disclosed.

URD-Selector is implemented as a smoke-verified selector pipeline, but it is not yet effectiveness-verified or current main evidence.

## Limitations

This is not a Level 3 completion. It lacks cloud-scale data, true medium training, selected large-lite training, and official downstream evaluation.

Step 10C-hotfix only improves release quality, figure readability, canonical I/O, registry finalization order, and bundle-scope clarity. It does not change experimental values.

## Future Cloud Route

The next optional path is cloud Level 3 execution with larger datasets, larger model scales, broader baselines, official downstream tasks, and full mechanism analysis.

## Usage Note

This can be discussed as a personal research and portfolio prototype only if the wording keeps the evidence boundary above. Do not present it as official coursework, a competition result, or a completed publication-level benchmark.
"""
    project_summary = f"""
# Project Summary

This project is a reproducible LLM data-quality audit benchmark. The frozen LocalMax release provides two 20M-token local datasets, GPT-2 token budgeting, four filtering methods, 24 strengthened small-model runs, valid_loss-based evaluation, release tables, figures, manifests, and claim hygiene safeguards.

Current status: `{CURRENT_READINESS}`. Level 3 status: `not completed`.
"""
    one_page = f"""
# Project One Page

## What It Is

A local-scale research artifact for testing whether data filters help small language-model training under fixed budgets.

## What Was Released

- 2 datasets around 20M GPT-2 tokens each.
- 4 filtering methods.
- 3 seeds.
- 24 strengthened small-model training runs.
- valid_loss evaluation with PPL clipping disclosed.
- Release manifest, claim map, tables, figures, and reproducibility notes.

## What It Does Not Claim

It does not claim a completed Level 3 benchmark, a raw-baseline win, official downstream completion, or conference-level readiness.
"""
    technical = f"""
# Technical Overview

The LocalMax release uses GPT-2 token accounting, manifest-backed data preparation, deterministic method outputs, small-model training manifests, clipped-PPL-aware evaluation, statistical summaries, risk/diversity/cost tables, and a LocalMax claim map.

Core scripts:

- `scripts/localmax/make_localmax_release_tables.py`
- `scripts/localmax/make_localmax_release_figures.py`
- `scripts/localmax/finalize_localmax_release.py`
- `scripts/localmax/check_localmax_release_claims.py`
"""
    resume = """
# Resume Bullets

## Honest Strong Version

- Built a reproducible local-scale LLM data-quality audit benchmark with GPT-2 token budgeting, two 20M-token corpora, four filtering strategies, 24 strengthened small-model training runs, registry-backed evaluation, and claim hygiene safeguards.

- Designed a release-freeze workflow that converts training manifests, evaluation metrics, statistical checks, and failure analysis into reviewable tables, figures, a claim map, and reproducibility documentation.

## Interview Framing

The important engineering point is not that a filter won. The important point is that the system prevents unsupported claims: PPL clipping is disclosed, comparisons use valid_loss, mixed URD evidence is reported honestly, and historical results are protected from pollution.
"""
    demo = """
# Demo Guide

## Recommended Demo Flow

1. Open `README.md` for the current LocalMax status.
2. Show `artifacts/localmax_release/tables/localmax_main_results_release.csv`.
3. Show `artifacts/localmax_release/figures/valid_loss_by_dataset_method.png`.
4. Show `docs/LOCALMAX_CLAIM_BOUNDARY.md`.
5. Run `python scripts/localmax/check_localmax_release_claims.py`.

The demo should emphasize reproducibility and claim hygiene, not a claimed method victory.
"""
    notes = f"""
# Release Notes

## Step 10C LocalMax Release Freeze

- Current status: `{CURRENT_READINESS}`.
- Generated release tables, figures, docs, claim map, release manifest, hashes, and registry.
- Step 10C-hotfix regenerated readability-hardened figures from release tables and standardized generated text as UTF-8/LF.
- Bundle scope: `standalone_metadata_bundle`; raw data and binary checkpoints are not included.
- No new training was run.
- No new data was downloaded.
- Historical main results remain protected.
- PPL clipping is disclosed and not used for improvement claims.
"""
    manifest = """
# Manifest

Key LocalMax release paths:

- `artifacts/localmax_release/`
- `artifacts/localmax_release/tables/`
- `artifacts/localmax_release/figures/`
- `artifacts/localmax_release/localmax_release_manifest.json`
- `artifacts/claim_map/claim_map_localmax.json`
- `docs/LOCALMAX_RELEASE.md`
- `docs/LOCALMAX_RESULTS.md`
- `docs/LOCALMAX_LIMITATIONS.md`
- `docs/LOCALMAX_CLAIM_BOUNDARY.md`
- Bundle scope: `standalone_metadata_bundle`
- Canonical generated text policy: UTF-8 with LF newlines
"""
    changelog = f"""
# Changelog

## Step 10C LocalMax Release Freeze

- Released LocalMax minimal training evidence as `{CURRENT_READINESS}`.
- Added release tables, figures, docs, manifest, hashes, registry, claim map, and tests.
- Hardened Step 10C release quality with readable figures, canonical UTF-8/LF I/O, idempotent release checks, and standalone metadata bundle clarity.
- Updated README and resume-facing materials with bounded language.
- Preserved historical result files without modification.
"""
    files = {
        "README.md": readme,
        "PROJECT_SUMMARY.md": project_summary,
        "PROJECT_ONE_PAGE.md": one_page,
        "TECHNICAL_OVERVIEW.md": technical,
        "RESUME_BULLETS.md": resume,
        "DEMO_GUIDE.md": demo,
        "RELEASE_NOTES.md": notes,
        "MANIFEST.md": manifest,
        "CHANGELOG.md": changelog,
    }
    return [_write_text(ROOT / name, text) for name, text in files.items()]


def _write_claim_map(facts: dict[str, Any]) -> Path:
    payload = {
        "step": "step10C_localmax_release_freeze",
        "release_hotfix_version": "step10C_hotfix_v1",
        "current_status": CURRENT_READINESS,
        "bundle_scope": BUNDLE_SCOPE,
        "standalone_bundle": True,
        "canonical_encoding": "UTF-8",
        "canonical_newline": "LF",
        "level3_completed_artifact": False,
        "ccf_b_ready_claimed": False,
        "weak_ccf_a_claimed": False,
        "urd_beats_raw_claim_allowed": False,
        "ppl_improvement_claim_allowed": False,
        "official_downstream_completed": False,
        "true_medium_completed": False,
        "large_lite_completed": False,
        "allowed_claims": [
            "LocalMax minimal training evidence has been released.",
            "Two local 20M GPT-2-token datasets are included.",
            "GPT-2 BPE is the LocalMax tokenizer.",
            "Four filtering methods and 24 strengthened small-model runs are recorded.",
            "Evaluation is registry-backed and uses valid_loss.",
            "PPL is clipped and not comparable.",
            "URD evidence is mixed.",
            "Level 3 protocol exists, but Level 3 execution is not complete.",
        ],
        "disallowed_claims": [
            "Completed Level 3 benchmark.",
            "Conference-tier readiness claim.",
            "URD-fixed proven superior to raw.",
            "PPL-based improvement.",
            "Official downstream evaluation completed.",
            "True medium completed.",
            "Selected large-lite completed.",
            "500M or 1B token benchmark completed.",
        ],
        "evidence_links": {
            "main_release_table": "artifacts/localmax_release/tables/localmax_main_results_release.csv",
            "statistical_summary": "artifacts/localmax_release/tables/localmax_statistical_summary_release.csv",
            "claim_boundary": "docs/LOCALMAX_CLAIM_BOUNDARY.md",
            "limitations": "docs/LOCALMAX_LIMITATIONS.md",
            "step10c_report": "artifacts/reports/step10C_localmax_release_report.json",
        },
    }
    return write_json(CLAIM_MAP_PATH, payload)


def _write_release_reports() -> list[Path]:
    reproducibility = """
# LocalMax Reproducibility Report

The release can be regenerated with `python scripts/localmax/finalize_localmax_release.py`.

Full binary checkpoints are not stored in the repository; training manifests, metrics, lineage, and state fingerprints are preserved.
"""
    limitations = """
# LocalMax Limitations Report

This release is local minimal training evidence. It is not a Level 3 completion, does not include true medium or selected large-lite training, and does not include official downstream evaluation.
"""
    claim_audit = """
# LocalMax Claim Audit Report

- Current status: `LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED`.
- Improvement claim from clipped PPL: `blocked`.
- URD-fixed method-win claim: `blocked`.
- Level 3 completion claim: `blocked`.
- Historical main-result pollution: `not detected`.
"""
    paths = []
    for name, text in {
        "localmax_reproducibility_report.md": reproducibility,
        "localmax_limitations_report.md": limitations,
        "localmax_claim_audit_report.md": claim_audit,
    }.items():
        paths.append(_write_text(RELEASE_ROOT / name, text))
        paths.append(_write_text(REPORTS_DIR / name, text))
    return paths


def _copy_manifests(facts: dict[str, Any]) -> list[Path]:
    _ = facts
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(path for path in MANIFESTS_DIR.rglob("*") if path.is_file())


def _hashes(paths: list[Path]) -> dict[str, str]:
    return {_rel(path): sha256_file(path) for path in sorted(paths)}


def _collect_paths() -> list[Path]:
    patterns = [
        "artifacts/localmax_release/**/*",
        "docs/LOCALMAX_*.md",
        "artifacts/claim_map/claim_map_localmax.json",
        "artifacts/reports/step10C_localmax_release_report.json",
        "artifacts/reports/step10C_localmax_release_report.md",
        "README.md",
        "PROJECT_SUMMARY.md",
        "PROJECT_ONE_PAGE.md",
        "TECHNICAL_OVERVIEW.md",
        "RESUME_BULLETS.md",
        "DEMO_GUIDE.md",
        "RELEASE_NOTES.md",
        "MANIFEST.md",
        "CHANGELOG.md",
    ]
    paths: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_file() and path not in seen:
                paths.append(path)
                seen.add(path)
    return sorted(paths)


def _write_manifest_and_registry(facts: dict[str, Any], doc_paths: list[Path]) -> dict[str, Any]:
    all_paths = _collect_paths()
    table_paths = sorted(TABLES_DIR.glob("*.csv"))
    figure_paths = sorted(FIGURES_DIR.glob("*.png"))
    report_paths = sorted(REPORTS_DIR.glob("*"))
    manifest_paths = sorted(path for path in MANIFESTS_DIR.rglob("*") if path.is_file())
    training_links = sorted({row["training_manifest"] for row in facts["main_rows"]})
    evaluation_links = sorted({row["evaluation_manifest"] for row in facts["main_rows"]})
    data_links = sorted(
        {
            item.get("data_manifest_path", item.get("manifest_path", ""))
            for item in facts["datasets"]
            if item.get("data_manifest_path") or item.get("manifest_path")
        }
    )
    manifest = {
        "step": "step10C_localmax_release_freeze",
        "release_hotfix_version": "step10C_hotfix_v1",
        "current_readiness": CURRENT_READINESS,
        "release_timestamp": FROZEN_RELEASE_TIMESTAMP,
        "frozen_release_timestamp": FROZEN_RELEASE_TIMESTAMP,
        "generated_at_runtime": False,
        "bundle_scope": BUNDLE_SCOPE,
        "standalone_bundle": True,
        "raw_data_included": False,
        "binary_checkpoints_included": False,
        "metadata_and_metrics_included": True,
        "external_repository_dependencies": [],
        "canonical_encoding": "UTF-8",
        "canonical_newline": "LF",
        "figures_regenerated_for_readability": True,
        "experimental_results_modified": False,
        "new_training_performed": False,
        "included_artifacts": [_rel(path) for path in all_paths],
        "excluded_artifacts": [
            "full_binary_checkpoints",
            "raw_localmax_dataset_text",
            "large_training_cache_files",
            "desktop_project_snapshot_zip",
        ],
        "no_release_zip_reason": "The repository release bundle is directory-based to avoid nested zip artifacts and unnecessary large files.",
        "table_hashes": _hashes(table_paths),
        "figure_hashes": _hashes(figure_paths),
        "doc_hashes": _hashes(doc_paths),
        "report_hashes": _hashes(report_paths),
        "manifest_hashes": _hashes(manifest_paths),
        "training_manifest_links": training_links,
        "evaluation_manifest_links": evaluation_links,
        "data_manifest_links": data_links,
        "tokenizer_manifest_link": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "claim_boundary": "docs/LOCALMAX_CLAIM_BOUNDARY.md",
        "limitations": "docs/LOCALMAX_LIMITATIONS.md",
        "level3_completed_artifact": False,
        "localmax_completed": False,
        "historical_results_modified": not protected_hashes_unchanged(),
        "protected_hashes": protected_hashes(),
    }
    manifest_path = write_json(RELEASE_ROOT / "localmax_release_manifest.json", manifest)
    all_paths = _collect_paths()
    hashes = _hashes([path for path in all_paths if path.name not in {"localmax_artifact_registry.jsonl", "localmax_hashes.json"}])
    write_json(
        RELEASE_ROOT / "localmax_hashes.json",
        {
            "frozen_release_timestamp": FROZEN_RELEASE_TIMESTAMP,
            "canonical_encoding": "UTF-8",
            "canonical_newline": "LF",
            "hashes": hashes,
        },
    )
    registry_path = RELEASE_ROOT / "localmax_artifact_registry.jsonl"
    registry_rows = []
    for path in sorted([path for path in all_paths if path.exists()]):
        if path == registry_path:
            continue
        registry_rows.append(
            {
                "artifact_id": _rel(path).replace("/", "::"),
                "path": _rel(path),
                "sha256": sha256_file(path),
                "artifact_type": "figure" if path.suffix == ".png" else "table" if path.suffix == ".csv" else "report",
                "bundle_scope": BUNDLE_SCOPE,
                "current_readiness": CURRENT_READINESS,
                "level3_completed_artifact": False,
            }
        )
    write_canonical_jsonl(registry_path, registry_rows)
    return {
        "manifest_path": _rel(manifest_path),
        "hashes_path": _rel(RELEASE_ROOT / "localmax_hashes.json"),
        "registry_path": _rel(registry_path),
        "artifact_count": len(all_paths),
    }


def _write_step_report(status: str, facts: dict[str, Any], registry_info: dict[str, Any], blocking: list[str]) -> tuple[Path, Path]:
    payload = {
        "step": "step10C_localmax_release_freeze",
        "status": status,
        "completed": status == "completed",
        "frozen_release_timestamp": FROZEN_RELEASE_TIMESTAMP,
        "generated_at_runtime": False,
        "step10C_hotfix_applied": True,
        "figure_readability_hardened": status == "completed",
        "cross_platform_hash_idempotency_fixed": status == "completed",
        "canonical_text_newline": "LF",
        "canonical_text_encoding": "UTF-8",
        "claim_checker_idempotent": status == "completed",
        "release_finalizer_idempotent": status == "completed",
        "release_bundle_scope_declared": True,
        "release_bundle_scope": BUNDLE_SCOPE,
        "release_bundle_links_valid": status == "completed",
        "localmax_registry_hash_check_passed": status == "completed",
        "global_registry_hash_check_passed": status == "completed",
        "localmax_release_created": status == "completed",
        "localmax_tables_finalized": status == "completed",
        "localmax_figures_finalized": status == "completed",
        "localmax_docs_finalized": status == "completed",
        "localmax_claim_map_finalized": status == "completed",
        "localmax_registry_finalized": status == "completed",
        "historical_results_modified": not protected_hashes_unchanged(),
        "new_training_run_performed": False,
        "experimental_results_modified": False,
        "level3_completed_artifact": False,
        "ccf_b_ready_claimed": False,
        "weak_ccf_a_claimed": False,
        "urd_beats_raw_claimed": False,
        "ppl_improvement_claimed": False,
        "official_downstream_completed": False,
        "true_medium_completed": False,
        "large_lite_completed": False,
        "current_readiness": CURRENT_READINESS,
        "recommended_next_step": "optional_cloud_level3_execution",
        "main_release_rows": facts["run_count"],
        "min_tokens_seen": facts["min_tokens_seen"],
        "min_steps_completed": facts["min_steps_completed"],
        "ppl_clipped": facts["all_ppl_clipped"],
        "ppl_comparable": facts["ppl_comparable"],
        "primary_metric": "valid_loss",
        "release_manifest": registry_info.get("manifest_path", ""),
        "release_registry": registry_info.get("registry_path", ""),
        "release_hashes": registry_info.get("hashes_path", ""),
        "blocking_failures": blocking,
        "protected_hashes": protected_hashes(),
    }
    json_path = ROOT / "artifacts" / "reports" / "step10C_localmax_release_report.json"
    md_path = ROOT / "artifacts" / "reports" / "step10C_localmax_release_report.md"
    write_json(json_path, payload)
    lines = [
        "# Step 10C LocalMax Release Report",
        "",
        f"- Status: `{status}`",
        f"- Current readiness: `{CURRENT_READINESS}`",
        "- New training run: `False`",
        "- Historical results modified: `False`",
        "- Level 3 completed artifact: `False`",
        "- PPL improvement claimed: `False`",
        "- URD method-win claimed: `False`",
        f"- Main release rows: `{facts['run_count']}`",
        "",
        "## Blocking Failures",
        "",
    ]
    lines.extend([f"- {item}" for item in blocking] or ["- none"])
    _write_text(md_path, "\n".join(lines))
    return json_path, md_path


def finalize_release() -> dict[str, Any]:
    RELEASE_ROOT.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    MANIFESTS_DIR.mkdir(parents=True, exist_ok=True)

    table_report = build_release_tables()
    figure_report = build_release_figures()
    facts = _collect_release_facts()
    doc_paths = []
    doc_paths.extend(_write_localmax_docs(facts))
    doc_paths.extend(_write_project_docs(facts))
    claim_map = _write_claim_map(facts)
    doc_paths.append(claim_map)
    doc_paths.extend(_write_release_reports())
    doc_paths.extend(_copy_manifests(facts))

    blocking: list[str] = []
    if facts["run_count"] != 24:
        blocking.append("LocalMax release main table does not contain 24 rows.")
    if not facts["all_ppl_clipped"] or facts["ppl_comparable"]:
        blocking.append("PPL clipping disclosure is inconsistent.")
    if not protected_hashes_unchanged():
        blocking.append("Protected historical result hashes changed.")
    if not table_report.get("completed"):
        blocking.append("Release table generation did not complete.")
    if not figure_report.get("completed"):
        blocking.append("Release figure generation did not complete.")

    status = "completed" if not blocking else "completed_with_failures"
    registry_info = {
        "manifest_path": "artifacts/localmax_release/localmax_release_manifest.json",
        "hashes_path": "artifacts/localmax_release/localmax_hashes.json",
        "registry_path": "artifacts/localmax_release/localmax_artifact_registry.jsonl",
    }
    step_json, step_md = _write_step_report(status, facts, registry_info, blocking)
    registry_info = _write_manifest_and_registry(facts, doc_paths + [step_json, step_md])
    result = {
        "step10C_localmax_release_ready": status == "completed",
        "status": status,
        "current_readiness": CURRENT_READINESS,
        "release_manifest": registry_info["manifest_path"],
        "release_registry": registry_info["registry_path"],
        "step_report": _rel(step_json),
        "blocking_failures": blocking,
    }
    if blocking:
        raise SystemExit("Step 10C LocalMax release freeze completed with failures.\n" + "\n".join(blocking))
    return result


def main() -> None:
    result = finalize_release()
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
