from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import csv
import json
from collections import Counter, defaultdict
from html import escape
from pathlib import Path
from statistics import mean
from typing import Any

from experiment_utils import root


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _float(row: dict[str, str], key: str) -> float | None:
    value = row.get(key, "")
    if value in {"", None}:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _svg_header(width: int, height: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="32" font-family="Arial" font-size="18" font-weight="bold">{escape(title)}</text>',
    ]


def _write_bar_svg(path: Path, title: str, values: list[tuple[str, float]], *, unit: str = "") -> None:
    height = max(180, 64 + 30 * len(values))
    width = 960
    max_value = max((abs(value) for _, value in values), default=1.0) or 1.0
    lines = _svg_header(width, height, title)
    for index, (label, value) in enumerate(values):
        y = 58 + index * 30
        bar_width = 520 * abs(value) / max_value
        color = "#4c78a8" if value >= 0 else "#e45756"
        lines.append(f'<text x="24" y="{y + 15}" font-family="Arial" font-size="12">{escape(label)}</text>')
        lines.append(f'<rect x="330" y="{y}" width="{bar_width:.1f}" height="18" fill="{color}"/>')
        lines.append(
            f'<text x="{340 + bar_width:.1f}" y="{y + 14}" font-family="Arial" font-size="11">{value:.4f}{escape(unit)}</text>'
        )
    lines.append("</svg>")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_status_svg(path: Path, status_rows: list[dict[str, str]]) -> None:
    values = []
    status_score = {
        "real_nonfallback": 3,
        "real_local_nonfallback": 3,
        "insufficient_streaming_sample": 1,
        "failed_due_to_network": -1,
        "failed_due_to_auth": -1,
        "failed_due_to_disk": -1,
        "failed_due_to_environment": -1,
        "configured_not_run": 0,
    }
    for row in status_rows:
        values.append((f"{row.get('dataset')} ({row.get('dataset_status')})", status_score.get(row.get("dataset_status", ""), 0)))
    _write_bar_svg(path, "Dataset Status Matrix", values)


def analyze() -> dict[str, Any]:
    cross_dir = root / "artifacts" / "cross_dataset"
    figure_dir = root / "artifacts" / "figures"
    rows = _read_csv(cross_dir / "cross_dataset_results.csv")
    status_rows = _read_csv(cross_dir / "dataset_status_matrix.csv")
    failures = _read_csv(cross_dir / "cross_dataset_failures.csv")
    completed = [row for row in rows if row.get("run_status") == "completed_training"]

    ppl_values = []
    keep_values = []
    shift_values = []
    by_dataset_method: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in completed:
        ppl = _float(row, "mean_ppl")
        keep = _float(row, "keep_rate")
        shift = _float(row, "distribution_shift_metric")
        label = f"{row.get('dataset')} / {row.get('method')}"
        if ppl is not None:
            by_dataset_method[(row.get("dataset", ""), row.get("method", ""))].append(ppl)
        if keep is not None:
            keep_values.append((label, keep))
        if shift is not None:
            shift_values.append((label, shift))
    for (dataset, method), values in sorted(by_dataset_method.items()):
        ppl_values.append((f"{dataset} / {method}", mean(values)))

    _write_bar_svg(figure_dir / "cross_dataset_method_comparison.svg", "Cross-Dataset Method Comparison (lower PPL is better)", ppl_values)
    _write_bar_svg(figure_dir / "cross_dataset_keep_rate.svg", "Cross-Dataset Keep Rate", keep_values)
    _write_bar_svg(figure_dir / "cross_dataset_distribution_shift.svg", "Cross-Dataset Distribution Shift Proxy", shift_values)
    _write_status_svg(figure_dir / "dataset_status_matrix.svg", status_rows)
    failure_counts = Counter(f"{row.get('dataset')} / {row.get('run_status')}" for row in failures)
    _write_bar_svg(
        figure_dir / "filter_failure_modes_by_dataset.svg",
        "Filter/Data Failure Modes By Dataset",
        [(label, float(count)) for label, count in sorted(failure_counts.items())],
    )

    mean_by_dataset_method = {
        (dataset, method): mean(values)
        for (dataset, method), values in by_dataset_method.items()
        if values
    }
    raw_statement = "insufficient multi-dataset evidence"
    hdqs_statement = "insufficient multi-dataset evidence"
    stable_statement = "insufficient multi-dataset evidence"
    datasets_with_raw = {
        row.get("dataset")
        for row in completed
        if row.get("method") == "raw" and _float(row, "mean_ppl") is not None
    }
    if datasets_with_raw:
        raw_statement = f"raw has completed rows on {len(datasets_with_raw)} dataset(s)"
    hdqs_datasets = {
        row.get("dataset")
        for row in completed
        if row.get("method") == "hdqspp_v3" and _float(row, "mean_ppl") is not None
    }
    if hdqs_datasets:
        hdqs_vs_raw = []
        for dataset in sorted(hdqs_datasets):
            raw_mean = mean_by_dataset_method.get((dataset, "raw"))
            hdqs_mean = mean_by_dataset_method.get((dataset, "hdqspp_v3"))
            if raw_mean is None or hdqs_mean is None:
                continue
            verdict = "below raw" if hdqs_mean < raw_mean else "above raw"
            hdqs_vs_raw.append(
                f"{dataset}: hdqspp_v3 mean PPL {hdqs_mean:.4f} is {verdict} "
                f"(raw {raw_mean:.4f})"
            )
        if hdqs_vs_raw and all("above raw" in item for item in hdqs_vs_raw):
            hdqs_statement = "HDQS++ v3 does not outperform raw by mean PPL on the completed datasets: " + "; ".join(hdqs_vs_raw)
        else:
            hdqs_statement = "HDQS++ v3 has mixed/preliminary behavior: " + "; ".join(hdqs_vs_raw)
    stable_methods = {
        method
        for method in ["raw", "random_same_keep_rate", "dedup_only"]
        if any(row.get("method") == method for row in completed)
    }
    if stable_methods:
        stable_statement = (
            "raw and dedup_only are the closest baselines in the completed rows; "
            "random_same_keep_rate is more variable on streaming samples"
        )

    report = [
        "# Cross-Dataset Audit",
        "",
        "This report expands the project from a single WikiText-2 audit candidate toward a multi-dataset audit benchmark.",
        "It follows `docs/REPORTING_CONTRACT.md` and does not claim supported improvement over raw across datasets.",
        "",
        "## Dataset Status",
        "",
        "| Dataset | Status | Scope | Completed rows | Failed rows | Failure reason |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in status_rows:
        report.append(
            f"| {row.get('dataset')} | `{row.get('dataset_status')}` | `{row.get('dataset_scope')}` | "
            f"{row.get('completed_training_rows')} | {row.get('failed_rows')} | {row.get('failure_reason')} |"
        )
    report.extend(
        [
            "",
            "## Audit Findings",
            "",
            f"- Raw baseline status: {raw_statement}.",
            f"- Raw/random/dedup stability: {stable_statement}.",
            f"- HDQS++ v3 status: {hdqs_statement}.",
            "- Perplexity comparisons across datasets are not direct method claims unless tokenizer hash, vocabulary size, parameter count, and token budget match.",
            "- Failed OpenWebText/C4 states, if present, are retained as audit evidence rather than hidden.",
            "",
            "## Generated Figures",
            "",
            "- `artifacts/figures/cross_dataset_method_comparison.svg`",
            "- `artifacts/figures/cross_dataset_keep_rate.svg`",
            "- `artifacts/figures/cross_dataset_distribution_shift.svg`",
            "- `artifacts/figures/dataset_status_matrix.svg`",
            "- `artifacts/figures/filter_failure_modes_by_dataset.svg`",
        ]
    )
    (root / "docs" / "CROSS_DATASET_AUDIT.md").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )
    analysis = {
        "completed_rows": len(completed),
        "failure_rows": len(failures),
        "dataset_statuses": status_rows,
        "raw_statement": raw_statement,
        "hdqspp_v3_statement": hdqs_statement,
        "baseline_stability_statement": stable_statement,
    }
    (cross_dir / "cross_dataset_analysis.json").write_text(
        json.dumps(analysis, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return analysis


def main() -> None:
    result = analyze()
    print(f"Cross-dataset completed rows: {result['completed_rows']}")
    print(f"Cross-dataset failure rows: {result['failure_rows']}")
    print("Cross-dataset audit: docs/CROSS_DATASET_AUDIT.md")


if __name__ == "__main__":
    main()
