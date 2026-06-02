from __future__ import annotations

import html
import json
from pathlib import Path


COLORS = ["#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2"]


def _prepare(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def write_line_chart(
    path: str | Path,
    series: dict[str, list[tuple[float, float]]],
    title: str,
    x_label: str,
    y_label: str,
) -> None:
    path = _prepare(path)
    width, height, margin = 760, 430, 62
    points = [point for values in series.values() for point in values]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if ymax == ymin:
        ymax += 1

    def px(value: float) -> float:
        return margin + (value - xmin) * (width - 2 * margin) / max(1e-12, xmax - xmin)

    def py(value: float) -> float:
        return height - margin - (value - ymin) * (height - 2 * margin) / max(1e-12, ymax - ymin)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" font-family="Arial" font-size="18">{html.escape(title)}</text>',
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#111827"/>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#111827"/>',
        f'<text x="{width / 2}" y="{height - 16}" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(x_label)}</text>',
        f'<text x="18" y="{height / 2}" text-anchor="middle" transform="rotate(-90 18 {height / 2})" font-family="Arial" font-size="13">{html.escape(y_label)}</text>',
    ]
    for index, (name, values) in enumerate(series.items()):
        color = COLORS[index % len(COLORS)]
        coords = " ".join(f"{px(x):.1f},{py(y):.1f}" for x, y in values)
        lines.append(
            f'<polyline points="{coords}" fill="none" stroke="{color}" stroke-width="2.5"/>'
        )
        lines.append(
            f'<text x="{width - margin - 160}" y="{margin + 18 * index}" font-family="Arial" font-size="12" fill="{color}">{html.escape(name)}</text>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_bar_chart(path: str | Path, rows: list[dict[str, object]], title: str) -> None:
    write_named_bar_chart(
        path,
        [
            (
                f"{row['implementation']} T={row['sequence_length']}",
                float(row["query_tokens_per_second"]),
            )
            for row in rows
        ],
        title,
        "Query tokens / second",
    )


def write_named_bar_chart(
    path: str | Path,
    rows: list[tuple[str, float]],
    title: str,
    y_label: str,
) -> None:
    path = _prepare(path)
    width, height, margin = 820, 450, 72
    vmax = max((value for _, value in rows), default=1.0)
    slot = (width - 2 * margin) / max(1, len(rows))
    bar_width = max(10, slot - 8)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" font-family="Arial" font-size="18">{html.escape(title)}</text>',
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#111827"/>',
        f'<text x="18" y="{height / 2}" text-anchor="middle" transform="rotate(-90 18 {height / 2})" font-family="Arial" font-size="13">{html.escape(y_label)}</text>',
    ]
    for index, (label, value) in enumerate(rows):
        bar_height = value * (height - 2 * margin) / max(1e-12, vmax)
        x = margin + index * slot + 4
        y = height - margin - bar_height
        lines.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" height="{bar_height:.1f}" fill="{COLORS[index % len(COLORS)]}"/>'
        )
        lines.append(
            f'<text x="{x + bar_width / 2:.1f}" y="{height - margin + 14}" text-anchor="end" transform="rotate(-38 {x + bar_width / 2:.1f} {height - margin + 14})" font-family="Arial" font-size="10">{html.escape(label)}</text>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_histogram(path: str | Path, values: list[float], title: str, bins: int = 10) -> None:
    if not values:
        values = [0.0]
    low, high = min(values), max(values)
    width = max(1e-12, high - low)
    counts = [0 for _ in range(bins)]
    for value in values:
        index = min(bins - 1, int((value - low) / width * bins))
        counts[index] += 1
    rows = [
        (f"{low + width * index / bins:.2f}", float(count)) for index, count in enumerate(counts)
    ]
    write_named_bar_chart(path, rows, title, "Documents")


def write_scatter_chart(
    path: str | Path,
    rows: list[tuple[str, float, float]],
    title: str,
    x_label: str,
    y_label: str,
) -> None:
    path = _prepare(path)
    width, height, margin = 760, 430, 70
    xs = [row[1] for row in rows]
    ys = [row[2] for row in rows]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax == xmin:
        xmax += 1
    if ymax == ymin:
        ymax += 1

    def px(value: float) -> float:
        return margin + (value - xmin) * (width - 2 * margin) / (xmax - xmin)

    def py(value: float) -> float:
        return height - margin - (value - ymin) * (height - 2 * margin) / (ymax - ymin)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="28" text-anchor="middle" font-family="Arial" font-size="18">{html.escape(title)}</text>',
        f'<line x1="{margin}" y1="{height - margin}" x2="{width - margin}" y2="{height - margin}" stroke="#111827"/>',
        f'<line x1="{margin}" y1="{margin}" x2="{margin}" y2="{height - margin}" stroke="#111827"/>',
        f'<text x="{width / 2}" y="{height - 16}" text-anchor="middle" font-family="Arial" font-size="13">{html.escape(x_label)}</text>',
        f'<text x="18" y="{height / 2}" text-anchor="middle" transform="rotate(-90 18 {height / 2})" font-family="Arial" font-size="13">{html.escape(y_label)}</text>',
    ]
    for index, (label, x, y) in enumerate(rows):
        color = COLORS[index % len(COLORS)]
        lines.append(f'<circle cx="{px(x):.1f}" cy="{py(y):.1f}" r="5" fill="{color}"/>')
        lines.append(
            f'<text x="{px(x) + 7:.1f}" y="{py(y) - 7:.1f}" font-family="Arial" font-size="11" fill="{color}">{html.escape(label)}</text>'
        )
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def generate_figures(payload: dict[str, object], output_dir: str | Path) -> None:
    output = Path(output_dir)
    runs = payload["model_runs"]
    write_line_chart(
        output / "training_curves.svg",
        {
            f"{run['variant']} seed={run['seed']}": [
                (point["step"], point["val_loss"]) for point in run["curve"]
            ]
            for run in runs
        },
        "Held-out validation loss",
        "Training step",
        "Validation loss",
    )
    write_bar_chart(
        output / "attention_throughput.svg",
        payload["attention_benchmark"]["rows"],
        "Auxiliary attention throughput (median)",
    )
    write_histogram(
        output / "quality_score_distribution.svg",
        [row["score"] for row in payload["quality_scores"]],
        "HDQS quality-score distribution",
    )
    variants = payload["data_quality_ablation"]
    summaries = payload["model_summary"]
    write_scatter_chart(
        output / "retention_vs_perplexity.svg",
        [
            (
                name,
                variants[name]["characters"] / max(1, variants["raw_noisy_baseline"]["characters"]),
                summary["final_val_perplexity"]["mean"],
            )
            for name, summary in summaries.items()
        ],
        "Retention versus held-out perplexity",
        "Character retention ratio",
        "Perplexity",
    )
    privacy = payload["privacy_report"]
    downstream = payload["downstream_report"]
    write_scatter_chart(
        output / "privacy_vs_utility.svg",
        [
            (
                "raw",
                float(privacy["raw_pii_hits"]),
                downstream["raw_noisy_baseline"]["next_char_accuracy"]["mean"],
            ),
            (
                "full",
                float(privacy["full_pipeline_pii_hits"]),
                downstream["full_pipeline"]["next_char_accuracy"]["mean"],
            ),
        ],
        "Synthetic privacy versus utility",
        "Residual PII-like hits",
        "Next-character accuracy",
    )
    write_named_bar_chart(
        output / "data_pipeline_summary.svg",
        [(name, float(metrics["documents"])) for name, metrics in variants.items()],
        "Documents retained by intervention",
        "Documents",
    )


def regenerate_figures_from_results(path: str | Path) -> None:
    results_path = Path(path)
    payload = json.loads(results_path.read_text(encoding="utf-8"))
    generate_figures(payload, results_path.parent)
