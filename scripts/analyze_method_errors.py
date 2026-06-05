from __future__ import annotations

import csv
import json
from html import escape
from pathlib import Path

from experiment_utils import root
from registry_utils import read_registry_jsonl


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _latest_training_rows() -> list[dict[str, str]]:
    latest: dict[tuple[str, str], dict[str, str]] = {}
    for row in read_registry_jsonl():
        if row["dataset_key"] != "wikitext2_paper" or row["model_size"] != "small":
            continue
        if row["run_status"] != "completed_training":
            continue
        if row["baseline_name"].startswith("ablation_"):
            continue
        key = (row["baseline_name"], row["seed"])
        latest[key] = row
    return list(latest.values())


def _component_correlation_svg(summary: dict[str, object], output: Path) -> None:
    correlations = summary.get("component_correlations_with_dev_loss_proxy", {})
    if not isinstance(correlations, dict):
        correlations = {}
    values = [(str(key), float(value)) for key, value in correlations.items()]
    max_abs = max([abs(value) for _, value in values] + [1.0])
    zero_x = 480
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="420">',
        "<desc>source=artifacts/diagnostics/hdqspp_failure_analysis.json</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="32" font-family="Arial" font-size="18">'
        "Method component correlation</text>",
        f'<line x1="{zero_x}" y1="56" x2="{zero_x}" y2="390" stroke="#999"/>',
    ]
    for index, (name, value) in enumerate(values):
        y = 68 + index * 36
        width = abs(value) / max_abs * 380
        x = zero_x if value >= 0 else zero_x - width
        color = "#e45756" if value >= 0 else "#59a14f"
        lines.append(
            f'<text x="24" y="{y + 15}" font-family="Arial" font-size="12">'
            f"{escape(name)}</text>"
        )
        lines.append(
            f'<rect x="{x:.1f}" y="{y}" width="{width:.1f}" height="22" '
            f'fill="{color}"/>'
        )
        lines.append(
            f'<text x="880" y="{y + 15}" font-family="Arial" font-size="12">'
            f"{value:.3f}</text>"
        )
    lines.append("</svg>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _distribution_shift_svg(summary: dict[str, object], output: Path) -> None:
    values = [
        ("v1 token JS vs raw", float(summary.get("token_js_hdqspp_vs_raw", 0))),
        ("v2 token JS vs raw", float(summary.get("token_js_hdqspp_v2_vs_raw", 0))),
        ("v1 length JS vs raw", float(summary.get("length_js_hdqspp_vs_raw", 0))),
        ("v2 length JS vs raw", float(summary.get("length_js_hdqspp_v2_vs_raw", 0))),
    ]
    max_value = max([value for _, value in values] + [1e-9])
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="280">',
        "<desc>source=artifacts/diagnostics/hdqspp_failure_analysis.json</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="32" font-family="Arial" font-size="18">'
        "Distribution shift after filtering</text>",
    ]
    for index, (name, value) in enumerate(values):
        y = 70 + index * 42
        width = value / max_value * 560
        lines.append(f'<text x="24" y="{y + 15}" font-family="Arial" font-size="12">{name}</text>')
        lines.append(f'<rect x="250" y="{y}" width="{width:.1f}" height="24" fill="#4c78a8"/>')
        lines.append(
            f'<text x="{260 + width:.1f}" y="{y + 16}" '
            f'font-family="Arial" font-size="12">{value:.6f}</text>'
        )
    lines.append("</svg>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _keep_rate_vs_ppl_svg(rows: list[dict[str, str]], output: Path) -> None:
    points = []
    for row in rows:
        try:
            points.append(
                (
                    row["baseline_name"],
                    float(row["retention_rate"]),
                    float(row["final_val_perplexity"]),
                )
            )
        except ValueError:
            continue
    if not points:
        return
    min_y = min(point[2] for point in points)
    max_y = max(point[2] for point in points)
    span_y = max(max_y - min_y, 1e-9)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="460">',
        "<desc>source=artifacts/runs/run_registry.csv</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="32" font-family="Arial" font-size="18">Keep rate vs validation PPL</text>',
        '<line x1="80" y1="390" x2="820" y2="390" stroke="#333"/>',
        '<line x1="80" y1="70" x2="80" y2="390" stroke="#333"/>',
    ]
    for name, keep_rate, ppl in points:
        x = 80 + keep_rate * 740
        y = 390 - ((ppl - min_y) / span_y) * 320
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#4c78a8" opacity="0.65"/>')
        lines.append(
            f'<text x="{x + 7:.1f}" y="{y + 4:.1f}" '
            f'font-family="Arial" font-size="10">{escape(name)}</text>'
        )
    lines.append("</svg>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    diagnostic_path = root / "artifacts" / "diagnostics" / "hdqspp_failure_analysis.csv"
    summary_path = root / "artifacts" / "diagnostics" / "hdqspp_failure_analysis.json"
    rows = _read_csv(diagnostic_path)
    if not rows or not summary_path.exists():
        raise SystemExit("Run scripts/diagnose_hdqspp.py before analyze_method_errors.py.")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    error_rows: list[dict[str, object]] = []
    dropped = [row for row in rows if row["kept_by_hdqspp"] == "False"]
    kept = [row for row in rows if row["kept_by_hdqspp"] == "True"]
    for row in sorted(dropped, key=lambda item: float(item["dev_loss_proxy"]))[:20]:
        error_rows.append({**row, "error_type": "v1_dropped_low_proxy_loss"})
    for row in sorted(kept, key=lambda item: float(item["hdqspp_score"]))[:20]:
        error_rows.append({**row, "error_type": "v1_kept_low_score"})
    output_dir = root / "artifacts" / "diagnostics"
    figure_dir = root / "artifacts" / "figures"
    csv_path = output_dir / "method_error_cases.csv"
    md_path = output_dir / "method_error_cases.md"
    _write_csv(csv_path, error_rows)
    md_path.write_text(
        "# Method Error Cases\n\n"
        "Examples are truncated and extracted from real WikiText-2 train documents.\n\n"
        "| Error type | Document | HDQS++ score | v2 score | Excerpt |\n"
        "|---|---:|---:|---:|---|\n"
        + "\n".join(
            f"| {row['error_type']} | {row['document_index']} | "
            f"{float(row['hdqspp_score']):.4f} | "
            f"{float(row['hdqspp_v2_score']):.4f} | {row['excerpt']} |"
            for row in error_rows[:24]
        )
        + "\n",
        encoding="utf-8",
    )
    _component_correlation_svg(summary, figure_dir / "method_component_correlation.svg")
    _distribution_shift_svg(summary, figure_dir / "distribution_shift_after_filtering.svg")
    _keep_rate_vs_ppl_svg(_latest_training_rows(), figure_dir / "keep_rate_vs_validation_ppl.svg")
    print(f"Method error cases: {len(error_rows)}")
    print(f"Method error report: {md_path}")


if __name__ == "__main__":
    main()
