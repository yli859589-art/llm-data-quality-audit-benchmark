from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

from localmax_v2_utils import (
    ROOT,
    V2_ANALYSIS,
    V2_DOWNSTREAM,
    V2_EVALUATION,
    V2_FILTERS,
    V2_RELEASE,
    V2_TABLES,
    V2_TRAINING,
    load_json,
    protected_hashes,
    protected_hashes_unchanged,
    read_csv,
    rel,
    sha256_file,
    status_payload,
    write_json,
    write_report,
    write_text,
)


RELEASE_STATUS = "LOCAL_MAX_V2_STRONG_EVIDENCE_RELEASED"


def _copy_file(src: Path, dst: Path) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return rel(dst)


def _copy_tree_files(src_root: Path, dst_root: Path, patterns: tuple[str, ...]) -> list[str]:
    copied: list[str] = []
    for pattern in patterns:
        for src in src_root.rglob(pattern):
            if src.is_file():
                dst = dst_root / src.relative_to(src_root)
                copied.append(_copy_file(src, dst))
    return sorted(set(copied))


def _all_release_files() -> list[Path]:
    return sorted([path for path in V2_RELEASE.rglob("*") if path.is_file()], key=lambda item: item.as_posix())


def _write_docs(readiness: dict[str, Any], eval_report: dict[str, Any]) -> list[str]:
    data_rows = read_csv(V2_TABLES / "localmax_v2_dataset_summary.csv")
    training_rows = read_csv(V2_TABLES / "localmax_v2_training_summary.csv")
    stats_rows = read_csv(V2_TABLES / "localmax_v2_statistical_tests.csv")
    failure_rows = read_csv(V2_TABLES / "localmax_v2_mechanism_results.csv")
    total_tokens = sum(int(row["actual_gpt2_tokens"]) for row in data_rows)
    total_training_tokens = sum(int(row["total_tokens_seen"]) for row in training_rows)
    best = eval_report.get("best_method_by_valid_nll", {})
    urd = eval_report.get("urd_fixed_vs_raw", {})
    docs: dict[str, str] = {}
    docs["README.md"] = f"""# LLM Data Quality Audit Benchmark

Current status: `LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED`

LocalMax V2 status: `{RELEASE_STATUS}`

Level 3 status: `not completed`

Bundle scope: `standalone_metadata_bundle`

This repository is a reproducible research artifact for auditing language-model pretraining data filters under controlled token budgets.

The project does **not** claim a completed Level 3 benchmark, publication-tier readiness, institutional affiliation, competition placement, official downstream completion, or a supported method win over raw training data.

The original LocalMax V1 release remains available as the minimal training evidence baseline. V1 uses valid_loss as the comparison metric; its PPL values are clipped and not comparable.

## LocalMax V2 Summary

- Data: 2 real non-fallback datasets, `{total_tokens}` GPT-2 tokens total.
- Methods: raw, exact_dedup, length_filter, urd_fixed.
- Training: 24 small-model runs, each >=1M tokens_seen.
- Model: small decoder LM, about 20.5M parameters, GPT-2 tokenizer, context length 256.
- Main comparison metric: `valid_nll_nats_per_token`.
- PPL is computed without clipping; no PPL-improvement claim is made unless supported by the tables.
- Level 3 remains unfinished.
- CCF-B readiness is not claimed.
- The release bundle excludes raw data and large binary checkpoints.

## Quick Start

```bash
python scripts/localmax_v2/finalize_localmax_v2_release.py
python scripts/localmax_v2/audit_lm_metric_correctness.py
python -m pytest tests/ -q
```

For the full grouped validation wrapper:

```bash
python scripts/run_all_checks.py --timeout 600
```

## Reproducibility Notes

The release directory contains metadata, metrics, tables, figures, reports, and copied manifests needed for review. It does not contain raw data text or full binary checkpoints.

Historical single-seed and smoke artifacts are retained for lineage, but they are not the LocalMax V2 main evidence.

URD-Selector is implemented as a smoke-verified selector pipeline, but it is not yet effectiveness-verified or current main evidence.

## Usage Note

This can be discussed as a personal research and portfolio prototype only if the wording keeps the evidence boundary above. Do not present it as official coursework, a competition result, or a completed publication-level benchmark.

See `docs/LOCALMAX_V2_RESULTS.md` and `artifacts/localmax_v2_release/`.
"""
    docs["PROJECT_SUMMARY.md"] = f"""# Project Summary

LocalMax V2 upgrades the earlier LocalMax release from 40M-token minimal evidence to a 200M-token local evidence benchmark.

It includes two 100M-token real dataset samples, four filtering methods, three seeds, and 24 registry-backed small-model training runs. The result is stronger local evidence, not a Level 3 or CCF-B-ready claim.
"""
    docs["PROJECT_ONE_PAGE.md"] = f"""# One Page Overview

LocalMax V2 evaluates data filtering for language-model pretraining under a fixed local budget: 2 datasets x 4 methods x 3 seeds, with 1M tokens_seen per run.

Best methods by valid NLL: `{best}`.

URD-fixed evidence is reported honestly: `{urd}`.
"""
    docs["TECHNICAL_OVERVIEW.md"] = f"""# Technical Overview

- Tokenizer: GPT-2 BPE.
- Datasets: OpenWebText V2 100M and C4 English V2 100M.
- Model: small decoder LM, context length 256.
- Training: 489 steps/run, 1,001,472 tokens_seen/run.
- Evaluation: valid NLL, log-PPL/PPL, paired seed differences, bootstrap CI, risk/diversity/cost, Pareto diagnostics.
"""
    docs["RESUME_BULLETS.md"] = """# Resume Bullets

- Earlier LocalMax V1 release: built a reproducible benchmark over two 20M-token corpora with 24 strengthened small-model training runs and claim hygiene safeguards.
- Built a reproducible 200M-token LLM data-quality auditing benchmark over OpenWebText and C4, comparing raw, exact dedup, length filtering, and URD-fixed across 24 controlled small-model training runs.
- Implemented GPT-2-tokenized data manifests, no-fallback verification, ID-based filtering artifacts, per-token NLL/PPL audit tests, bootstrap confidence intervals, mechanism analysis, and release-bundle integrity checks.
- Preserved honest claim boundaries: reports local evidence only and avoids unsupported publication-readiness, leaderboard, or URD-superiority wording.
"""
    docs["docs/LOCALMAX_V2_RESULTS.md"] = f"""# LocalMax V2 Results

Status: `{RELEASE_STATUS}`

Data scale: `{total_tokens}` GPT-2 tokens across two non-fallback datasets.

Training: 24/24 core runs completed; total training tokens_seen across method/seed runs: `{total_training_tokens}`.

Main metric: `valid_nll_nats_per_token`.

Best method per dataset by valid NLL: `{best}`.

URD vs raw: `{urd}`.
"""
    docs["docs/LOCALMAX_V2_LIMITATIONS.md"] = """# LocalMax V2 Limitations

- This is strong local evidence, not Level 3 completion.
- The model is small, not true medium or large-lite.
- Downstream subset is recorded as unavailable; no official downstream claim is made.
- Results are bounded to 100M-token samples and 1M tokens_seen per run.
- URD superiority is not claimed unless statistical tables support it.
"""
    docs["docs/LOCALMAX_V2_REPRODUCIBILITY.md"] = """# LocalMax V2 Reproducibility

Run order:

1. `python scripts/localmax_v2/check_localmax_v2_environment.py`
2. `python scripts/localmax_v2/audit_lm_metric_correctness.py`
3. `python scripts/localmax_v2/prepare_localmax_v2_data.py --config configs/localmax_v2/data_matrix.yaml`
4. `python scripts/localmax_v2/run_localmax_v2_filters.py --config configs/localmax_v2/filter_matrix.yaml`
5. `python scripts/localmax_v2/benchmark_training_throughput.py`
6. `python scripts/localmax_v2/run_localmax_v2_training.py --config configs/localmax_v2/training_matrix.yaml`
7. `python scripts/localmax_v2/run_localmax_v2_evaluation.py --config configs/localmax_v2/evaluation_matrix.yaml`
8. `python scripts/localmax_v2/run_localmax_v2_downstream.py --config configs/localmax_v2/downstream_matrix.yaml`
9. `python scripts/localmax_v2/run_localmax_v2_analysis.py --config configs/localmax_v2/mechanism_matrix.yaml`
10. `python scripts/localmax_v2/finalize_localmax_v2_execution.py`
11. `python scripts/localmax_v2/finalize_localmax_v2_release.py`

Text artifacts use UTF-8/LF canonical writing. PNG hashes are platform-dependent; source CSVs and generation scripts are the reproducibility anchors.
"""
    docs["docs/LOCALMAX_V2_CLAIM_BOUNDARY.md"] = """# LocalMax V2 Claim Boundary

Allowed:

- LocalMax V2 strong local evidence released.
- 2 x 100M GPT-2-token non-fallback dataset samples.
- 24 small-model runs with >=1M tokens_seen/run.
- Valid NLL/log-PPL/PPL metric audit passed.

Forbidden current claims:

- Forbidden current claim: Level 3 completed is not allowed.
- Forbidden current claim: CCF-B ready is not allowed.
- Forbidden current claim: weak CCF-A achieved is not allowed.
- Forbidden current claim: SOTA is not allowed.
- Forbidden current claim: true medium or large-lite completed is not allowed.
- Forbidden current claim: official downstream completed is not allowed.
- Forbidden current claim: URD beats raw unless the statistical table explicitly permits the claim; the current V2 tables do not permit it.
"""
    docs["docs/LOCALMAX_V2_DATA_CARD.md"] = "# LocalMax V2 Data Card\n\n" + "\n".join(
        f"- {row['dataset_id']}: {row['actual_gpt2_tokens']} GPT-2 tokens, {row['document_count']} documents, fallback={row['fallback_used']}"
        for row in data_rows
    ) + "\n"
    docs["docs/LOCALMAX_V2_MODEL_CARD.md"] = """# LocalMax V2 Model Card

- Architecture: decoder-only language model.
- Scale: small.
- Parameters: about 20.5M.
- Context length: 256.
- Tokenizer: GPT-2.
- Training budget: 1,001,472 tokens_seen/run.
- Not a medium or large-lite model.
"""
    docs["docs/LOCALMAX_V2_FAILURE_ANALYSIS.md"] = "# LocalMax V2 Failure Analysis\n\n" + (
        "\n".join(f"- {row.get('dataset_id')}: {row.get('failure_type')} - {row.get('reason')}" for row in failure_rows)
        if failure_rows else "- No failure taxonomy rows were generated.\n"
    )
    docs["docs/LOCALMAX_V2_FUTURE_CLOUD_LEVEL3.md"] = """# Future Cloud Level 3

Next steps for true Level 3 require larger token budgets, true medium/large-lite model scales, official downstream evaluation, and cloud-scale reproducibility. LocalMax V2 should be treated as the final local evidence release, not as Level 3 completion.
"""
    written = []
    for rel_path, text in docs.items():
        written.append(rel(write_text(ROOT / rel_path, text)))
    return written


def _make_figures() -> list[str]:
    figs = V2_RELEASE / "figures"
    figs.mkdir(parents=True, exist_ok=True)
    summary = read_csv(V2_TABLES / "localmax_v2_method_summary.csv")
    main = read_csv(V2_TABLES / "localmax_v2_main_results.csv")
    data = read_csv(V2_TABLES / "localmax_v2_dataset_summary.csv")
    training = read_csv(V2_TABLES / "localmax_v2_training_summary.csv")
    risk = read_csv(V2_TABLES / "localmax_v2_risk_diversity_cost.csv")
    paired = read_csv(V2_TABLES / "localmax_v2_statistical_tests.csv")
    downstream = read_csv(V2_TABLES / "localmax_v2_downstream_subset.csv")
    mechanism = read_csv(V2_TABLES / "localmax_v2_mechanism_results.csv")
    outputs: list[str] = []

    def save(name: str) -> None:
        plt.tight_layout()
        path = figs / name
        plt.savefig(path, dpi=140)
        plt.close()
        outputs.append(rel(path))

    for dataset in sorted({row["dataset_id"] for row in summary}):
        rows = [row for row in summary if row["dataset_id"] == dataset]
        plt.figure(figsize=(9, 5))
        plt.bar([row["method_name"] for row in rows], [float(row["mean_valid_nll_nats_per_token"]) for row in rows])
        plt.ylabel("Valid NLL (lower is better)")
        plt.title(f"LocalMax V2 validation NLL - {dataset}")
        plt.xticks(rotation=25, ha="right")
        save(f"validation_nll_by_method_{dataset}.png")

    plt.figure(figsize=(9, 5))
    for dataset in sorted({row["dataset_id"] for row in main}):
        rows = [row for row in main if row["dataset_id"] == dataset]
        xs = list(range(len(rows)))
        plt.scatter(xs, [float(row["valid_nll_nats_per_token"]) for row in rows], label=dataset, s=18)
    plt.ylabel("Valid NLL (lower is better)")
    plt.title("LocalMax V2 seed stability")
    plt.legend()
    save("seed_stability.png")

    plt.figure(figsize=(9, 5))
    urd_rows = [row for row in paired if row["comparison"] == "urd_fixed_vs_raw"]
    plt.bar([row["dataset_id"] for row in urd_rows], [float(row["mean_paired_nll_improvement"]) for row in urd_rows])
    plt.axhline(0, color="black", linewidth=1)
    plt.ylabel("Raw NLL - URD NLL")
    plt.title("URD vs raw paired difference")
    save("urd_vs_raw_paired_difference.png")

    plt.figure(figsize=(9, 5))
    for row in risk:
        plt.scatter(float(row["risk"]), float(row["diversity"]), s=max(20, float(row["cost"]) / 3500), label=f"{row['dataset_id']}:{row['method_name']}")
    plt.xlabel("Risk proxy")
    plt.ylabel("Diversity proxy")
    plt.title("Risk-diversity-cost diagnostic")
    plt.legend(fontsize=6, loc="best")
    save("risk_diversity_cost.png")

    plt.figure(figsize=(9, 5))
    plt.scatter([float(row["risk"]) for row in risk], [-float(row["mean_valid_nll_nats_per_token"]) for row in risk])
    plt.xlabel("Risk proxy")
    plt.ylabel("Utility proxy (-valid NLL)")
    plt.title("Local Pareto diagnostic")
    save("pareto.png")

    plt.figure(figsize=(8, 5))
    plt.bar([row["dataset_id"] for row in data], [int(row["actual_gpt2_tokens"]) / 1_000_000 for row in data])
    plt.ylabel("GPT-2 tokens (millions)")
    plt.title("LocalMax V2 data scale")
    save("data_scale_summary.png")

    plt.figure(figsize=(8, 5))
    labels = [f"{row['dataset_id']}:{row['method_name']}" for row in training]
    plt.bar(range(len(labels)), [int(row["min_tokens_seen"]) / 1_000_000 for row in training])
    plt.xticks(range(len(labels)), labels, rotation=70, ha="right", fontsize=7)
    plt.ylabel("Min tokens_seen/run (millions)")
    plt.title("Training budget summary")
    save("training_budget_summary.png")

    plt.figure(figsize=(8, 4))
    plt.bar([row["benchmark"] for row in downstream], [1 if row["status"] == "completed" else 0 for row in downstream])
    plt.ylabel("Completed")
    plt.title("Downstream subset status")
    save("downstream_subset.png")

    plt.figure(figsize=(8, 4))
    counts: dict[str, int] = {}
    for row in mechanism:
        counts[row.get("failure_type", "none")] = counts.get(row.get("failure_type", "none"), 0) + 1
    if counts:
        plt.bar(list(counts.keys()), list(counts.values()))
    plt.title("Mechanism/failure summary")
    plt.xticks(rotation=25, ha="right")
    save("mechanism_summary.png")
    return outputs


def _refresh_v1_claim_report() -> None:
    subprocess.run(
        [sys.executable, "scripts/localmax/check_localmax_release_claims.py"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _refresh_legacy_localmax_registry_hashes() -> None:
    """Keep the V1 standalone registry consistent after V2 updates shared docs."""
    registry_path = ROOT / "artifacts" / "localmax_release" / "localmax_artifact_registry.jsonl"
    hashes_path = ROOT / "artifacts" / "localmax_release" / "localmax_hashes.json"
    if not registry_path.exists():
        return
    rows = [
        json.loads(line)
        for line in registry_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if hashes_path.exists():
        hashes_payload = load_json(hashes_path)
        hashes = dict(hashes_payload.get("hashes", {}))
        for row in rows:
            artifact_path = ROOT / row["path"]
            if not artifact_path.exists():
                continue
            if artifact_path.name in {"localmax_artifact_registry.jsonl", "localmax_hashes.json"}:
                continue
            hashes[row["path"]] = sha256_file(artifact_path)
        hashes_payload["hashes"] = dict(sorted(hashes.items()))
        write_json(hashes_path, hashes_payload)
    for row in rows:
        artifact_path = ROOT / row["path"]
        if artifact_path.exists():
            row["sha256"] = sha256_file(artifact_path)
    write_text(
        registry_path,
        "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows),
    )


def _copy_bundle_metadata() -> list[str]:
    copied: list[str] = []
    for src in V2_TABLES.glob("*.csv"):
        copied.append(_copy_file(src, V2_RELEASE / "tables" / src.name))
    copied.extend(_copy_tree_files(ROOT / "artifacts" / "localmax_v2_data", V2_RELEASE / "manifests" / "data", ("*.json", "*.md")))
    tokenizer_manifest = ROOT / "artifacts" / "localmax_tokenizers" / "gpt2" / "tokenizer_manifest.json"
    if tokenizer_manifest.exists():
        copied.append(_copy_file(tokenizer_manifest, V2_RELEASE / "manifests" / "tokenizer" / "gpt2" / "tokenizer_manifest.json"))
    copied.extend(_copy_tree_files(V2_FILTERS, V2_RELEASE / "manifests" / "filters", ("*.json",)))
    copied.extend(_copy_tree_files(V2_TRAINING, V2_RELEASE / "manifests" / "training", ("*.json",)))
    copied.extend(_copy_tree_files(V2_EVALUATION, V2_RELEASE / "manifests" / "evaluation", ("*.json", "*.csv")))
    copied.extend(_copy_tree_files(V2_ANALYSIS, V2_RELEASE / "manifests" / "analysis", ("*.json", "*.csv")))
    copied.extend(_copy_tree_files(V2_DOWNSTREAM, V2_RELEASE / "manifests" / "downstream", ("*.json", "*.csv")))
    return copied


def main() -> None:
    readiness = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_readiness_report.json")
    if readiness.get("localmax_v2_core_gates_passed") is not True:
        raise SystemExit("LocalMax V2 core gates must pass before release freeze.")
    eval_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_evaluation_report.json")
    V2_RELEASE.mkdir(parents=True, exist_ok=True)
    copied = _copy_bundle_metadata()
    docs = _write_docs(readiness, eval_report)
    _refresh_v1_claim_report()
    _refresh_legacy_localmax_registry_hashes()
    figures = _make_figures()
    release_manifest = {
        "step": "step10C_localmax_v2_release",
        "status": "completed",
        "current_readiness": RELEASE_STATUS,
        "bundle_scope": "standalone_metadata_bundle",
        "standalone_bundle": True,
        "raw_data_included": False,
        "binary_checkpoints_included": False,
        "metadata_and_metrics_included": True,
        "level3_completed_artifact": False,
        "ccf_b_ready_claimed": False,
        "weak_ccf_a_claimed": False,
        "sota_claimed": False,
        "official_downstream_completed": False,
        "true_medium_completed": False,
        "large_lite_completed": False,
        "experimental_results_modified": False,
        "historical_results_modified": not protected_hashes_unchanged(),
        "protected_hashes": protected_hashes(),
        "copied_metadata_files": copied,
        "docs": docs,
        "figures": figures,
    }
    write_json(V2_RELEASE / "localmax_v2_release_manifest.json", release_manifest)
    bundle_errors = []
    required = [
        V2_RELEASE / "tables" / "localmax_v2_main_results.csv",
        V2_RELEASE / "localmax_v2_release_manifest.json",
        V2_RELEASE / "localmax_v2_artifact_registry.jsonl",
        V2_RELEASE / "localmax_v2_hashes.json",
    ]
    for path in required:
        if not path.exists():
            bundle_errors.append(f"Missing required release file: {rel(path)}")
    bundle_report = {
        "status": "passed" if not bundle_errors else "failed",
        "bundle_scope": "standalone_metadata_bundle",
        "release_bundle_links_valid": not bundle_errors,
        "raw_data_included": False,
        "binary_checkpoints_included": False,
        "metadata_file_count": len(copied),
        "figure_count": len(figures),
        "errors": bundle_errors,
    }
    write_json(V2_RELEASE / "reports" / "release_bundle_integrity_report.json", bundle_report)
    write_text(V2_RELEASE / "reports" / "release_bundle_integrity_report.md", "# LocalMax V2 Release Bundle Integrity\n\n- Status: `" + bundle_report["status"] + "`\n")
    excluded_registry_files = {
        (V2_RELEASE / "localmax_v2_artifact_registry.jsonl").resolve(),
        (V2_RELEASE / "localmax_v2_hashes.json").resolve(),
    }
    registry_rows = []
    for path in _all_release_files():
        if path.resolve() in excluded_registry_files:
            continue
        registry_rows.append(
            {
                "path": rel(path),
                "sha256": sha256_file(path),
                "size_bytes": path.stat().st_size,
                "artifact_type": path.suffix.lower().lstrip(".") or "file",
            }
        )
    registry_path = V2_RELEASE / "localmax_v2_artifact_registry.jsonl"
    write_text(registry_path, "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in registry_rows))
    hashes = {row["path"]: row["sha256"] for row in registry_rows}
    write_json(V2_RELEASE / "localmax_v2_hashes.json", hashes)
    report = status_payload(
        "release",
        not bundle_errors,
        bundle_errors,
        {
            "status": "completed" if not bundle_errors else "blocked",
            "current_readiness": RELEASE_STATUS if not bundle_errors else "LOCAL_MAX_V2_RELEASE_BLOCKED",
            "step10C_v2_executed": not bundle_errors,
            "localmax_v2_release_ready": not bundle_errors,
            "release_manifest": "artifacts/localmax_v2_release/localmax_v2_release_manifest.json",
            "release_registry": "artifacts/localmax_v2_release/localmax_v2_artifact_registry.jsonl",
            "release_hashes": "artifacts/localmax_v2_release/localmax_v2_hashes.json",
            "bundle_scope": "standalone_metadata_bundle",
            "tables_finalized": True,
            "figures_finalized": len(figures) >= 10,
            "docs_finalized": True,
            "historical_results_modified": not protected_hashes_unchanged(),
            "protected_hashes": protected_hashes(),
        },
    )
    write_report(report, "step10C_localmax_v2_release_report", "Step 10C LocalMax V2 Release Report")
    print(json.dumps({"localmax_v2_release_ready": not bundle_errors, "current_readiness": report["current_readiness"], "figures": len(figures)}))
    if bundle_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
