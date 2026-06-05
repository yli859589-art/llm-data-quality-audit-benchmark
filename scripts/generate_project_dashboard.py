from __future__ import annotations

from _bootstrap import bootstrap, build_subprocess_env

bootstrap()

import csv
import json
import subprocess
import sys
from collections import Counter
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

from experiment_utils import root


METHOD_ORDER = [
    "raw",
    "random_same_keep_rate",
    "dedup_only",
    "length_filter",
    "hdqspp",
    "hdqspp_v2",
    "hdqspp_v3",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _float(row: dict[str, Any], field: str) -> float | None:
    value = row.get(field, "")
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value: Any, digits: int = 4) -> str:
    if value in {"", None}:
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _svg_header(width: int, height: int, title: str, source: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f"<desc>source={escape(source)}; generated_by_script=scripts/generate_project_dashboard.py</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="24" y="34" font-family="Arial" font-size="19">{escape(title)}</text>',
    ]


def _box(lines: list[str], x: int, y: int, w: int, h: int, label: str, color: str = "#e8f0fe") -> None:
    lines.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}" stroke="#555"/>')
    lines.append(f'<text x="{x + 12}" y="{y + 28}" font-family="Arial" font-size="13">{escape(label)}</text>')


def _arrow(lines: list[str], x1: int, y1: int, x2: int, y2: int) -> None:
    lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#555" marker-end="url(#arrow)"/>')


def _pipeline_svg() -> str:
    lines = _svg_header(980, 250, "Project pipeline", "artifacts/data/wikitext2_paper/data_manifest.json")
    lines.extend(
        [
            '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth"><path d="M0,0 L0,6 L9,3 z" fill="#555"/></marker></defs>',
        ]
    )
    labels = [
        "WikiText-2 real split",
        "fair tokenizer/model",
        "completed training",
        "registry + lineage",
        "stats + dashboard",
    ]
    x = 24
    for index, label in enumerate(labels):
        _box(lines, x + index * 185, 92, 150, 62, label)
        if index < len(labels) - 1:
            _arrow(lines, x + index * 185 + 150, 123, x + (index + 1) * 185, 123)
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _protocol_svg() -> str:
    lines = _svg_header(980, 290, "Benchmark protocol", "configs/experiments/dev.yaml")
    labels = [
        ("dataset_status=real_nonfallback", "#d6f5d6"),
        ("dataset_scope=official_split", "#d6f5d6"),
        ("same tokenizer/vocab/params", "#e8f0fe"),
        ("train_tokens=1228800", "#e8f0fe"),
        ("evaluated_validation_tokens=53248", "#e8f0fe"),
        ("3 seeds, trend-only claims", "#fff2cc"),
    ]
    for index, (label, color) in enumerate(labels):
        _box(lines, 40 + (index % 3) * 300, 78 + (index // 3) * 92, 250, 58, label, color)
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _leaderboard_svg(stats_rows: list[dict[str, str]]) -> str:
    by_name = {row.get("baseline_name", ""): row for row in stats_rows}
    values = []
    for name in METHOD_ORDER:
        row = by_name.get(name)
        if not row:
            continue
        mean_ppl = _float(row, "mean")
        if mean_ppl is not None:
            values.append((name, mean_ppl))
    if not values:
        return "\n".join(_svg_header(760, 170, "Main results leaderboard", "artifacts/stats/main_results.csv") + ["</svg>"]) + "\n"
    max_ppl = max(value for _, value in values)
    best = min(value for _, value in values)
    height = 70 + len(values) * 34
    lines = _svg_header(1020, height, "Main results leaderboard: lower PPL is better", "artifacts/stats/main_results.csv")
    for index, (name, value) in enumerate(values):
        y = 66 + index * 34
        width = 600 * value / max_ppl
        color = "#59a14f" if value == best else "#f28e2b" if name == "hdqspp_v3" else "#bab0ac"
        lines.append(f'<text x="24" y="{y + 16}" font-family="Arial" font-size="12">{escape(name)}</text>')
        lines.append(f'<rect x="270" y="{y}" width="{width:.1f}" height="22" fill="{color}"/>')
        lines.append(f'<text x="{280 + width:.1f}" y="{y + 15}" font-family="Arial" font-size="11">{value:.4f}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _failure_svg(stats_rows: list[dict[str, str]], method_rows: list[dict[str, str]]) -> str:
    by_name = {row.get("baseline_name", ""): row for row in stats_rows}
    raw = _float(by_name.get("raw", {}), "mean") or 0.0
    rows = []
    for name in ["length_filter", "hdqspp", "hdqspp_v2", "hdqspp_v3", "random_same_keep_rate", "dedup_only"]:
        value = _float(by_name.get(name, {}), "mean")
        if value is not None:
            rows.append((name, value - raw))
    height = max(230, 74 + len(rows) * 34)
    lines = _svg_header(980, height, "Failure mode summary vs raw", "artifacts/stats/main_results.csv")
    lines.append('<text x="24" y="56" font-family="Arial" font-size="12">Positive delta means worse PPL than raw.</text>')
    for index, (name, delta) in enumerate(rows):
        y = 82 + index * 34
        color = "#e15759" if delta > 0 else "#59a14f"
        width = min(620, abs(delta) * 220)
        lines.append(f'<text x="24" y="{y + 15}" font-family="Arial" font-size="12">{escape(name)}</text>')
        lines.append(f'<rect x="280" y="{y}" width="{width:.1f}" height="22" fill="{color}"/>')
        lines.append(f'<text x="{290 + width:.1f}" y="{y + 15}" font-family="Arial" font-size="11">{delta:+.4f}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _lineage_svg(registry_rows: list[dict[str, str]]) -> str:
    statuses = Counter(row.get("run_status", "") for row in registry_rows)
    values = sorted(statuses.items())
    height = max(220, 76 + len(values) * 34)
    max_count = max((count for _, count in values), default=1)
    lines = _svg_header(920, height, "Artifact lineage overview by run status", "artifacts/runs/run_registry.csv")
    for index, (status, count) in enumerate(values):
        y = 72 + index * 34
        width = 560 * count / max_count
        color = "#4c78a8" if status == "completed_training" else "#bab0ac"
        lines.append(f'<text x="24" y="{y + 15}" font-family="Arial" font-size="12">{escape(status)}</text>')
        lines.append(f'<rect x="280" y="{y}" width="{width:.1f}" height="22" fill="{color}"/>')
        lines.append(f'<text x="{290 + width:.1f}" y="{y + 15}" font-family="Arial" font-size="11">{count}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> None:
    subprocess.run([sys.executable, "scripts/generate_method_dashboard.py"], cwd=root, env=build_subprocess_env(), check=True)
    figures = root / "artifacts" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    stats_rows = _read_csv(root / "artifacts" / "stats" / "main_results.csv")
    method_rows = _read_csv(root / "artifacts" / "stats" / "method_comparison_summary.csv")
    registry_rows = _read_csv(root / "artifacts" / "runs" / "run_registry.csv")
    cross_status_rows = _read_csv(root / "artifacts" / "cross_dataset" / "dataset_status_matrix.csv")
    readiness = _read_json(root / "artifacts" / "experiment_readiness_report.json")

    (figures / "project_pipeline.svg").write_text(_pipeline_svg(), encoding="utf-8")
    (figures / "benchmark_protocol.svg").write_text(_protocol_svg(), encoding="utf-8")
    (figures / "main_results_leaderboard.svg").write_text(_leaderboard_svg(stats_rows), encoding="utf-8")
    (figures / "failure_mode_summary.svg").write_text(_failure_svg(stats_rows, method_rows), encoding="utf-8")
    (figures / "artifact_lineage_overview.svg").write_text(_lineage_svg(registry_rows), encoding="utf-8")

    by_name = {row.get("baseline_name", ""): row for row in stats_rows}
    lines = [
        "# Experiment Dashboard",
        "",
        f"- Readiness: `{readiness.get('readiness_level', 'EXPERIMENT-CANDIDATE')}`",
        f"- Benchmark scope status: `{readiness.get('benchmark_scope_status', 'single_dataset_candidate')}`",
        "- Method status: `honest_audit_framework`",
        "- Secondary method finding: `hdqspp_v3_improves_over_v2_trend_but_not_raw`",
        "- CCF-C ready: `false`",
        "- Reporting contract: `docs/REPORTING_CONTRACT.md`",
        "",
        "## Main Results Snapshot",
        "",
        "| Method | Mean PPL | CI | Status |",
        "|---|---:|---|---|",
    ]
    for name in METHOD_ORDER:
        row = by_name.get(name)
        if not row:
            continue
        status = "best current baseline" if name == "raw" else "completed_training"
        lines.append(
            f"| `{name}` | {_fmt(row.get('mean'))} | "
            f"[{_fmt(row.get('ci95_low'))}, {_fmt(row.get('ci95_high'))}] | {status} |"
        )
    if cross_status_rows:
        lines.extend(
            [
                "",
                "## Cross-Dataset Status",
                "",
                "| Dataset | Status | Scope | Completed rows | Failed rows |",
                "|---|---|---|---:|---:|",
            ]
        )
        for row in cross_status_rows:
            lines.append(
                f"| `{row.get('dataset', '')}` | `{row.get('dataset_status', '')}` | "
                f"`{row.get('dataset_scope', '')}` | {row.get('completed_training_rows', '')} | "
                f"{row.get('failed_rows', '')} |"
            )
    lines.extend(
        [
            "",
            "## Figures",
            "",
            "- `artifacts/figures/project_pipeline.svg`",
            "- `artifacts/figures/benchmark_protocol.svg`",
            "- `artifacts/figures/method_comparison_ci.svg`",
            "- `artifacts/figures/main_results_leaderboard.svg`",
            "- `artifacts/figures/failure_mode_summary.svg`",
            "- `artifacts/figures/artifact_lineage_overview.svg`",
            "- `artifacts/figures/cross_dataset_method_comparison.svg`",
            "- `artifacts/figures/dataset_status_matrix.svg`",
            "",
            "## Interpretation",
            "",
            "The current WikiText-2 small-model evidence shows raw as the strongest mean PPL baseline. "
            "HDQS++ v3 improves over v2 as a secondary trend, but it does not support a method claim over raw.",
            "",
            "3B adds OpenWebText and C4 English real streaming samples. They are bounded samples, "
            "and cross-dataset tables preserve completed, lightweight, failed, and configured states.",
            "",
            "The project value is the audit trail: real data, fair baselines, append-only registry, "
            "artifact lineage, failure cases, and reproducible release checks.",
        ]
    )
    (root / "docs" / "EXPERIMENT_DASHBOARD.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print("Project dashboard generated.")


if __name__ == "__main__":
    main()
