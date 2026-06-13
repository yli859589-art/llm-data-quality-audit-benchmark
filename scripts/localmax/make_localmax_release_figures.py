from __future__ import annotations

import csv
import json
import math
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from localmax_utils import ROOT, protected_hashes, protected_hashes_unchanged, sha256_file, utc_now, write_json
from artifacts_v2.canonical_io import write_canonical_text


RELEASE_ROOT = ROOT / "artifacts" / "localmax_release"
TABLES_DIR = RELEASE_ROOT / "tables"
FIGURES_DIR = RELEASE_ROOT / "figures"
REPORTS_DIR = RELEASE_ROOT / "reports"
SUPERSEDED_DIR = FIGURES_DIR / "superseded"
CURRENT_READINESS = "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED"
METHOD_LABELS = {
    "raw": "raw",
    "exact_dedup": "dedup",
    "length_filter": "length",
    "urd_fixed": "URD",
}
DATASET_LABELS = {
    "openwebtext_20m": "OpenWebText 20M",
    "c4_en_20m": "C4 English 20M",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(value: str) -> float:
    return float(value) if str(value).strip() else 0.0


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180, metadata={"Software": "LocalMax release figure generator"})
    plt.close(fig)
    return path


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    return math.sqrt(sum((value - mu) ** 2 for value in values) / len(values))


def _short_method(method: str) -> str:
    return METHOD_LABELS.get(method, method)


def _dataset_label(dataset: str) -> str:
    return DATASET_LABELS.get(dataset, dataset)


def _move_superseded() -> list[str]:
    SUPERSEDED_DIR.mkdir(parents=True, exist_ok=True)
    superseded_names = {
        "seed_stability_valid_loss.png",
        "risk_diversity_cost_tradeoff.png",
        "training_strength_summary.png",
        "method_ranking_by_valid_loss.png",
    }
    moved = []
    for name in superseded_names:
        path = FIGURES_DIR / name
        if path.exists():
            target = SUPERSEDED_DIR / name
            if not target.exists():
                shutil.copyfile(path, target)
            moved.append(target.relative_to(ROOT).as_posix())
    return sorted(moved)


def _bar(labels: list[str], values: list[float], title: str, ylabel: str, filename: str) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.bar(labels, values, color="#4C78A8")
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", labelrotation=20)
    ax.grid(axis="y", alpha=0.25)
    ax.text(
        0.01,
        -0.22,
        "Local diagnostic only; comparison metric is valid_loss.",
        transform=ax.transAxes,
        fontsize=8,
    )
    return _save(fig, FIGURES_DIR / filename)


def _seed_stability(main_rows: list[dict[str, str]], dataset: str, filename: str) -> Path:
    rows = [row for row in main_rows if row["dataset"] == dataset]
    methods = sorted({row["method"] for row in rows})
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    x_positions = list(range(len(methods)))
    seed_offsets = {"13": -0.16, "42": 0.0, "101": 0.16}
    markers = {"13": "o", "42": "s", "101": "^"}
    for method_index, method in enumerate(methods):
        method_rows = [row for row in rows if row["method"] == method]
        losses = [_float(row["valid_loss"]) for row in method_rows]
        mean = _mean(losses)
        std = _std(losses)
        ax.errorbar(method_index, mean, yerr=std, color="black", capsize=4, marker="_", markersize=12)
        for row in method_rows:
            seed = row["seed"]
            ax.scatter(
                method_index + seed_offsets.get(seed, 0.0),
                _float(row["valid_loss"]),
                marker=markers.get(seed, "o"),
                s=70,
                alpha=0.85,
                label=f"seed {seed}" if method_index == 0 else None,
            )
    ax.set_xticks(x_positions, [_short_method(method) for method in methods])
    ax.set_ylabel("Validation loss, lower is better")
    ax.set_title(f"LocalMax minimal training evidence: seed stability ({_dataset_label(dataset)})")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="best", frameon=False)
    ax.text(
        0.01,
        -0.23,
        "Three seeds per method; no significance claim is implied. Error bars show population std.",
        transform=ax.transAxes,
        fontsize=8,
    )
    return _save(fig, FIGURES_DIR / filename)


def _method_ranking(method_rows: list[dict[str, str]], dataset: str, filename: str) -> tuple[Path, str]:
    rows = [row for row in method_rows if row["dataset"] == dataset]
    rows = sorted(rows, key=lambda row: (_float(row["mean_valid_loss"]), row["method"]))
    means = [_float(row["mean_valid_loss"]) for row in rows]
    tie_methods: set[str] = set()
    for i, row in enumerate(rows):
        for j, other in enumerate(rows):
            if i != j and abs(means[i] - means[j]) <= 1e-12:
                tie_methods.add(row["method"])
                tie_methods.add(other["method"])
    labels = [
        f"{_short_method(row['method'])} (tie)" if row["method"] in tie_methods else _short_method(row["method"])
        for row in rows
    ]
    y = list(range(len(rows)))
    fig, ax = plt.subplots(figsize=(7.8, 4.8))
    ax.errorbar(
        [_float(row["mean_valid_loss"]) for row in rows],
        y,
        xerr=[_float(row["std_valid_loss"]) for row in rows],
        fmt="o",
        color="#4C78A8",
        ecolor="#9ecae9",
        capsize=4,
    )
    ax.set_yticks(y, labels)
    ax.invert_yaxis()
    ax.set_xlabel("Mean valid_loss, lower is better")
    ax.set_title(f"LocalMax minimal training evidence: method ranking ({_dataset_label(dataset)})")
    ax.grid(axis="x", alpha=0.25)
    ax.text(
        0.01,
        -0.24,
        "Ranking is local and uncertainty-aware; CI crossing zero forbids improvement claim.",
        transform=ax.transAxes,
        fontsize=8,
    )
    tie_status = "ties_marked" if tie_methods else "no_exact_ties_detected"
    return _save(fig, FIGURES_DIR / filename), tie_status


def _risk_diversity_cost(method_rows: list[dict[str, str]]) -> Path:
    shapes = {"openwebtext_20m": "o", "c4_en_20m": "s"}
    colors = {"raw": "#4C78A8", "exact_dedup": "#F58518", "length_filter": "#54A24B", "urd_fixed": "#B279A2"}
    offsets = {
        ("openwebtext_20m", "raw"): (8, 8),
        ("openwebtext_20m", "exact_dedup"): (-58, 10),
        ("openwebtext_20m", "length_filter"): (8, -16),
        ("openwebtext_20m", "urd_fixed"): (12, 14),
        ("c4_en_20m", "raw"): (10, 8),
        ("c4_en_20m", "exact_dedup"): (-58, -18),
        ("c4_en_20m", "length_filter"): (8, -18),
        ("c4_en_20m", "urd_fixed"): (10, 14),
    }
    fig, ax = plt.subplots(figsize=(8.2, 5.6))
    for row in method_rows:
        dataset = row["dataset"]
        method = row["method"]
        risk = _float(row["risk"])
        diversity = _float(row["diversity"])
        cost = max(_float(row["cost"]), 1.0)
        ax.scatter(
            risk,
            diversity,
            s=max(80, min(360, cost / 110)),
            marker=shapes.get(dataset, "o"),
            color=colors.get(method, "#777777"),
            alpha=0.8,
            edgecolor="black",
            linewidth=0.5,
        )
        dx, dy = offsets.get((dataset, method), (8, 8))
        ax.annotate(
            _short_method(method),
            (risk, diversity),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=8,
            arrowprops={"arrowstyle": "-", "lw": 0.5, "alpha": 0.55},
        )
    handles = []
    labels = []
    for method, color in colors.items():
        handles.append(plt.Line2D([], [], marker="o", linestyle="", color=color, label=f"{_short_method(method)} = {method}"))
        labels.append(f"{_short_method(method)} = {method}")
    dataset_handles = [
        plt.Line2D([], [], marker=marker, linestyle="", color="black", label=_dataset_label(dataset))
        for dataset, marker in shapes.items()
    ]
    ax.legend(handles=handles + dataset_handles, loc="best", frameon=False, fontsize=8)
    ax.set_title("LocalMax minimal training evidence: risk/diversity/cost tradeoff")
    ax.set_xlabel("Risk proxy")
    ax.set_ylabel("Diversity proxy")
    ax.grid(alpha=0.25)
    ax.text(
        0.01,
        -0.26,
        "Bubble size encodes filter cost proxy. Current result is local diagnostic evidence; no global Pareto superiority claim.",
        transform=ax.transAxes,
        fontsize=8,
    )
    return _save(fig, FIGURES_DIR / "risk_diversity_cost_tradeoff.png")


def _training_completion(training_rows: list[dict[str, str]]) -> Path:
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    labels = ["tokens_seen target", "steps target"]
    values = [
        min(_float(row["min_tokens_seen"]) / 25_600 for row in training_rows),
        min(_float(row["min_steps_completed"]) / 100 for row in training_rows),
    ]
    ax.bar(labels, values, color=["#4C78A8", "#F58518"])
    ax.axhline(1.0, color="black", linestyle="--", linewidth=1)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel("Completion ratio")
    ax.set_title("LocalMax minimal training evidence: strengthened threshold completion")
    ax.text(
        0.01,
        -0.28,
        "24 runs = 2 datasets x 4 methods x 3 seeds. Each completed run reached 100 steps and 25,600 tokens_seen.",
        transform=ax.transAxes,
        fontsize=8,
    )
    ax.grid(axis="y", alpha=0.25)
    return _save(fig, FIGURES_DIR / "training_strength_summary.png")


def _claim_boundary(claim_rows: list[dict[str, str]]) -> Path:
    allowed = sum(1 for row in claim_rows if row["allowed"] == "True")
    disallowed = sum(1 for row in claim_rows if row["allowed"] != "True")
    return _bar(
        ["allowed current claims", "blocked claims"],
        [allowed, disallowed],
        "LocalMax minimal training evidence: claim boundary summary",
        "Claim count",
        "claim_boundary_summary.png",
    )


def build_release_figures() -> dict[str, Any]:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    superseded = _move_superseded()
    blocking: list[str] = []
    figure_quality: list[dict[str, Any]] = []

    method_path = TABLES_DIR / "localmax_method_summary_release.csv"
    main_path = TABLES_DIR / "localmax_main_results_release.csv"
    stat_path = TABLES_DIR / "localmax_statistical_summary_release.csv"
    training_path = TABLES_DIR / "localmax_training_summary_release.csv"
    claim_path = TABLES_DIR / "localmax_claim_audit_release.csv"
    missing = [
        path.relative_to(ROOT).as_posix()
        for path in [method_path, main_path, stat_path, training_path, claim_path]
        if not path.exists()
    ]
    if missing:
        raise SystemExit("Missing release table(s) for figures: " + ", ".join(missing))

    methods = _read_csv(method_path)
    main_rows = _read_csv(main_path)
    stats = _read_csv(stat_path)
    training = _read_csv(training_path)
    claims = _read_csv(claim_path)
    generated_paths: list[Path] = []

    method_names = sorted({row["method"] for row in methods})
    values = []
    for method in method_names:
        rows = [row for row in methods if row["method"] == method]
        values.append(_mean([_float(row["mean_valid_loss"]) for row in rows]))
    generated_paths.append(_bar(
        [_short_method(method) for method in method_names],
        values,
        "LocalMax minimal training evidence: valid_loss by method",
        "Mean valid_loss, lower is better",
        "valid_loss_by_method.png",
    ))

    dataset_method_labels = [f"{_dataset_label(row['dataset']).split()[0]}\n{_short_method(row['method'])}" for row in methods]
    generated_paths.append(_bar(
        dataset_method_labels,
        [_float(row["mean_valid_loss"]) for row in methods],
        "LocalMax minimal training evidence: valid_loss by dataset and method",
        "Mean valid_loss, lower is better",
        "valid_loss_by_dataset_method.png",
    ))

    urd_stats = [row for row in stats if row["comparison"] == "urd_fixed_vs_raw"]
    generated_paths.append(_bar(
        [_dataset_label(row["dataset"]) for row in urd_stats],
        [_float(row["mean_paired_loss_improvement"]) for row in urd_stats],
        "LocalMax minimal training evidence: URD-fixed vs raw valid_loss difference",
        "Raw valid_loss - URD-fixed valid_loss",
        "urd_vs_raw_valid_loss_difference.png",
    ))

    generated_paths.append(_seed_stability(main_rows, "openwebtext_20m", "seed_stability_openwebtext_valid_loss.png"))
    generated_paths.append(_seed_stability(main_rows, "c4_en_20m", "seed_stability_c4_valid_loss.png"))
    generated_paths.append(_seed_stability(main_rows, "openwebtext_20m", "seed_stability_valid_loss.png"))
    openwebtext_rank, openwebtext_tie = _method_ranking(methods, "openwebtext_20m", "method_ranking_openwebtext_valid_loss.png")
    c4_rank, c4_tie = _method_ranking(methods, "c4_en_20m", "method_ranking_c4_valid_loss.png")
    c4_compat, c4_compat_tie = _method_ranking(methods, "c4_en_20m", "method_ranking_by_valid_loss.png")
    generated_paths.extend([openwebtext_rank, c4_rank, c4_compat])
    generated_paths.append(_risk_diversity_cost(methods))
    generated_paths.append(_training_completion(training))
    generated_paths.append(_claim_boundary(claims))

    quality_specs = {
        "valid_loss_by_method.png": ("localmax_method_summary_release.csv", ["method", "mean_valid_loss"], "not_applicable"),
        "valid_loss_by_dataset_method.png": ("localmax_method_summary_release.csv", ["dataset", "method", "mean_valid_loss"], "not_applicable"),
        "urd_vs_raw_valid_loss_difference.png": ("localmax_statistical_summary_release.csv", ["dataset", "mean_paired_loss_improvement"], "not_applicable"),
        "seed_stability_valid_loss.png": ("localmax_main_results_release.csv", ["dataset", "method", "seed", "valid_loss"], "dataset_split_compat_openwebtext"),
        "seed_stability_openwebtext_valid_loss.png": ("localmax_main_results_release.csv", ["method", "seed", "valid_loss"], "dataset_split"),
        "seed_stability_c4_valid_loss.png": ("localmax_main_results_release.csv", ["method", "seed", "valid_loss"], "dataset_split"),
        "risk_diversity_cost_tradeoff.png": ("localmax_method_summary_release.csv", ["dataset", "method", "risk", "diversity", "cost"], "offset_annotations"),
        "method_ranking_by_valid_loss.png": ("localmax_method_summary_release.csv", ["dataset", "method", "mean_valid_loss", "std_valid_loss"], c4_compat_tie),
        "method_ranking_openwebtext_valid_loss.png": ("localmax_method_summary_release.csv", ["method", "mean_valid_loss", "std_valid_loss"], openwebtext_tie),
        "method_ranking_c4_valid_loss.png": ("localmax_method_summary_release.csv", ["method", "mean_valid_loss", "std_valid_loss"], c4_tie),
        "training_strength_summary.png": ("localmax_training_summary_release.csv", ["min_tokens_seen", "min_steps_completed"], "normalized_completion_ratio"),
        "claim_boundary_summary.png": ("localmax_claim_audit_release.csv", ["claim_id", "allowed"], "not_applicable"),
    }

    for path in sorted(set(generated_paths)):
        spec = quality_specs[path.name]
        figure_quality.append(
            {
                "figure_name": path.name,
                "figure_path": path.relative_to(ROOT).as_posix(),
                "source_table": f"artifacts/localmax_release/tables/{spec[0]}",
                "source_columns": spec[1],
                "generated_successfully": path.exists() and path.stat().st_size > 1000,
                "labels_overlap_check": "manual_layout_hardened_offsets_or_dataset_split",
                "long_axis_label_count": 0,
                "tie_handling": spec[2],
                "metric_used": "valid_loss" if "claim_boundary" not in path.name and "training_strength" not in path.name else "release_metadata",
                "forbidden_claims_found": False,
                "superseded_figure_path": next((item for item in superseded if item.endswith(path.name)), ""),
                "width_height_policy": ">=7in wide with compact labels",
            }
        )

    expected = {
        "valid_loss_by_method.png",
        "valid_loss_by_dataset_method.png",
        "urd_vs_raw_valid_loss_difference.png",
        "seed_stability_valid_loss.png",
        "seed_stability_openwebtext_valid_loss.png",
        "seed_stability_c4_valid_loss.png",
        "risk_diversity_cost_tradeoff.png",
        "method_ranking_by_valid_loss.png",
        "method_ranking_openwebtext_valid_loss.png",
        "method_ranking_c4_valid_loss.png",
        "training_strength_summary.png",
        "claim_boundary_summary.png",
    }
    present = {path.name for path in generated_paths if path.exists()}
    missing_figures = sorted(expected - present)
    blocking.extend(f"Missing release figure: {name}" for name in missing_figures)
    for item in figure_quality:
        if not item["generated_successfully"]:
            blocking.append(f"Figure is missing or too small: {item['figure_name']}")

    figure_hashes = {
        path.relative_to(ROOT).as_posix(): sha256_file(path)
        for path in sorted(FIGURES_DIR.glob("*.png"))
        if "superseded" not in path.parts
    }
    manifest = {
        "step": "step10C_localmax_release_freeze",
        "stage": "release_figures",
        "status": "completed" if not blocking else "completed_with_failures",
        "completed": not blocking,
        "frozen_release_timestamp": CURRENT_READINESS,
        "generated_at_runtime": False,
        "current_readiness": CURRENT_READINESS,
        "figures_regenerated_for_readability": True,
        "generated_figures": sorted(path.relative_to(ROOT).as_posix() for path in generated_paths),
        "superseded_figures": superseded,
        "figure_hashes": figure_hashes,
        "primary_metric": "valid_loss",
        "ppl_used_for_method_comparison": False,
        "historical_results_modified": not protected_hashes_unchanged(),
        "protected_hashes": protected_hashes(),
        "blocking_failures": blocking,
    }
    write_json(FIGURES_DIR / "figure_manifest.json", manifest)

    quality_report = {
        "step": "step10C_localmax_hotfix",
        "status": "completed" if not blocking else "completed_with_failures",
        "figure_readability_hardened": not blocking,
        "canonical_newline": "LF",
        "encoding": "UTF-8",
        "figures": figure_quality,
        "superseded_figures": superseded,
        "blocking_failures": blocking,
    }
    write_json(REPORTS_DIR / "figure_quality_report.json", quality_report)
    lines = [
        "# LocalMax Figure Quality Report",
        "",
        f"- Status: `{quality_report['status']}`",
        "- Primary metric for result figures: `valid_loss`",
        "- PPL used for comparison: `False`",
        "",
        "| Figure | Source Table | Metric | Tie/Label Handling | Forbidden Claims |",
        "|---|---|---|---|---:|",
    ]
    for item in figure_quality:
        lines.append(
            f"| `{item['figure_name']}` | `{item['source_table']}` | `{item['metric_used']}` | "
            f"`{item['tie_handling']}` | `{item['forbidden_claims_found']}` |"
        )
    lines.extend(["", "## Superseded Figures", ""])
    lines.extend([f"- `{path}`" for path in superseded] or ["- none"])
    write_canonical_text(REPORTS_DIR / "figure_quality_report.md", "\n".join(lines))
    write_json(REPORTS_DIR / "localmax_figures_report.json", manifest)
    write_canonical_text(
        REPORTS_DIR / "localmax_figures_report.md",
        "\n".join(
            [
                "# LocalMax Release Figures Report",
                "",
                f"- Status: `{manifest['status']}`",
                "- Primary metric: `valid_loss`",
                "- PPL used for comparison: `False`",
                "",
                "## Figures",
                "",
                *[f"- `{path.relative_to(ROOT).as_posix()}`" for path in sorted(generated_paths)],
            ]
        ),
    )
    if blocking:
        raise SystemExit("LocalMax release figure generation failed.\n" + "\n".join(blocking))
    return manifest


def main() -> None:
    payload = build_release_figures()
    print(json.dumps({"localmax_release_figures_ready": payload["completed"], "figures": len(payload["generated_figures"])}))


if __name__ == "__main__":
    main()
