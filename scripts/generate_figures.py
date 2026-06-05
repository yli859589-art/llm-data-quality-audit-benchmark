from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import csv
import hashlib
from html import escape
from pathlib import Path

from experiment_utils import root


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _hash(path: Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _svg_header(width: int, height: int, title: str, source: Path, script: str) -> list[str]:
    source_rel = source.relative_to(root).as_posix() if source.exists() else source.as_posix()
    desc = (
        f"generated_by_script={script}; "
        f"source_artifact={source_rel}; "
        f"source_artifact_hash={_hash(source)}"
    )
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        f"<desc>{escape(desc)}</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="24" y="32" font-family="Arial" font-size="18">{escape(title)}</text>',
    ]


def _empty_svg(title: str, reason: str, source: Path) -> str:
    lines = _svg_header(900, 180, title, source, "scripts/generate_figures.py")
    lines.extend(
        [
            '<rect x="24" y="58" width="820" height="72" fill="#f7f7f7" stroke="#cccccc"/>',
            f'<text x="42" y="91" font-family="Arial" font-size="14">{escape(reason)}</text>',
            '<text x="42" y="116" font-family="Arial" font-size="12" fill="#555555">'
            "No synthetic or fabricated values were drawn.</text>",
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def _baseline_retention_svg(rows: list[dict[str, str]], source: Path) -> str:
    unique = []
    seen = set()
    for row in rows:
        key = (row.get("dataset_key", ""), row.get("baseline_name", ""))
        if key not in seen and row.get("run_status") != "skipped":
            seen.add(key)
            unique.append(row)
    width = 900
    height = max(220, 50 + 24 * len(unique))
    labels_width = 290
    lines = _svg_header(
        width,
        height,
        "Baseline retention rates",
        source,
        "scripts/generate_figures.py",
    )
    for index, row in enumerate(unique):
        y = 56 + index * 24
        try:
            retention = float(row.get("retention_rate", "0"))
        except ValueError:
            retention = 0.0
        bar_width = int(max(0.0, min(1.0, retention)) * 500)
        label = f"{row.get('dataset_key', '')} / {row.get('baseline_name', '')}"
        lines.append(
            f'<text x="20" y="{y + 14}" font-family="Arial" font-size="11">{escape(label)}</text>'
        )
        lines.append(
            f'<rect x="{labels_width}" y="{y}" width="{bar_width}" height="16" fill="#4c78a8"/>'
        )
        lines.append(
            f'<text x="{labels_width + bar_width + 8}" y="{y + 13}" '
            f'font-family="Arial" font-size="11">{retention:.2f}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _seed_ci_svg(rows: list[dict[str, str]], source: Path) -> str:
    if not rows:
        return _empty_svg("Seed confidence intervals", "Missing stats/main_results.csv.", source)
    width = 960
    height = max(240, 80 + 42 * len(rows))
    values = []
    for row in rows:
        try:
            mean = float(row["mean"])
            low = float(row["ci95_low"])
            high = float(row["ci95_high"])
        except (KeyError, ValueError):
            continue
        values.append((row.get("baseline_name", ""), mean, low, high))
    if not values:
        return _empty_svg(
            "Seed confidence intervals",
            "Stats table exists but has no numeric confidence intervals.",
            source,
        )
    min_x = min(low for _, _, low, _ in values)
    max_x = max(high for _, _, _, high in values)
    span = max(max_x - min_x, 1e-6)

    def scale(value: float) -> float:
        return 250 + ((value - min_x) / span) * 620

    lines = _svg_header(
        width,
        height,
        "Seed confidence intervals (validation PPL)",
        source,
        "scripts/generate_figures.py",
    )
    lines.append('<line x1="250" y1="58" x2="870" y2="58" stroke="#cccccc"/>')
    lines.append(
        f'<text x="250" y="52" font-family="Arial" font-size="11">{min_x:.2f}</text>'
    )
    lines.append(
        f'<text x="832" y="52" font-family="Arial" font-size="11">{max_x:.2f}</text>'
    )
    for index, (label, mean_value, low, high) in enumerate(values):
        y = 86 + index * 42
        lines.append(
            f'<text x="24" y="{y + 4}" font-family="Arial" font-size="13">{escape(label)}</text>'
        )
        lines.append(
            f'<line x1="{scale(low):.1f}" y1="{y}" x2="{scale(high):.1f}" '
            f'y2="{y}" stroke="#4c78a8" stroke-width="4"/>'
        )
        lines.append(
            f'<circle cx="{scale(mean_value):.1f}" cy="{y}" r="6" fill="#e45756"/>'
        )
        lines.append(
            f'<text x="880" y="{y + 4}" font-family="Arial" font-size="12">{mean_value:.2f}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _ablation_svg(rows: list[dict[str, str]], source: Path) -> str:
    if not rows:
        return _empty_svg("Ablation effects", "Missing ablation_table.csv.", source)
    values = []
    for row in rows:
        try:
            delta = float(row.get("delta_output_tokens_vs_full", ""))
        except ValueError:
            continue
        values.append((row.get("variant", ""), delta, row.get("safe_claim_level", "")))
    if not values:
        return _empty_svg(
            "Ablation effects",
            "Ablation table has no numeric output-token deltas.",
            source,
        )
    width = 980
    height = max(260, 82 + 30 * len(values))
    max_abs = max(abs(delta) for _, delta, _ in values) or 1.0
    zero_x = 470

    def scale(delta: float) -> float:
        return zero_x + (delta / max_abs) * 360

    lines = _svg_header(
        width,
        height,
        "HDQS++ dev ablation effects (output-token delta)",
        source,
        "scripts/generate_figures.py",
    )
    lines.append(
        f'<line x1="{zero_x}" y1="58" x2="{zero_x}" '
        f'y2="{height - 24}" stroke="#999999"/>'
    )
    lines.append(
        '<text x="610" y="58" font-family="Arial" font-size="12">'
        "positive = more output tokens than full HDQS++</text>"
    )
    for index, (variant, delta, claim) in enumerate(values):
        y = 88 + index * 30
        x2 = scale(delta)
        color = "#e45756" if delta > 0 else "#59a14f"
        x = min(zero_x, x2)
        width_bar = abs(x2 - zero_x)
        lines.append(
            f'<text x="24" y="{y + 5}" font-family="Arial" font-size="12">{escape(variant)}</text>'
        )
        lines.append(
            f'<rect x="{x:.1f}" y="{y - 9}" width="{width_bar:.1f}" height="18" fill="{color}"/>'
        )
        lines.append(
            f'<text x="840" y="{y + 5}" font-family="Arial" font-size="11">'
            f'{delta:.3f} | {escape(claim)}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _privacy_utility_svg(rows: list[dict[str, str]], source: Path) -> str:
    points = []
    for row in rows:
        try:
            privacy = float(row.get("privacy_metric", ""))
            utility = float(row.get("model_quality_metric", ""))
        except ValueError:
            continue
        if row.get("run_status") == "completed_training":
            points.append((row.get("baseline_name", ""), privacy, utility))
    if not points:
        return _empty_svg(
            "Privacy utility tradeoff",
            "No completed-training rows contain both privacy_metric and model_quality_metric.",
            source,
        )
    width = 900
    height = 520
    min_x = min(point[1] for point in points)
    max_x = max(point[1] for point in points)
    min_y = min(point[2] for point in points)
    max_y = max(point[2] for point in points)
    x_span = max(max_x - min_x, 1e-6)
    y_span = max(max_y - min_y, 1e-6)

    def sx(value: float) -> float:
        return 90 + ((value - min_x) / x_span) * 700

    def sy(value: float) -> float:
        return 430 - ((value - min_y) / y_span) * 330

    lines = _svg_header(
        width,
        height,
        "Privacy utility tradeoff",
        source,
        "scripts/generate_figures.py",
    )
    lines.append('<line x1="90" y1="430" x2="790" y2="430" stroke="#333333"/>')
    lines.append('<line x1="90" y1="100" x2="90" y2="430" stroke="#333333"/>')
    for label, privacy, utility in points:
        lines.append(
            f'<circle cx="{sx(privacy):.1f}" cy="{sy(utility):.1f}" '
            'r="5" fill="#4c78a8"/>'
        )
        lines.append(
            f'<text x="{sx(privacy) + 8:.1f}" y="{sy(utility) + 4:.1f}" '
            f'font-family="Arial" font-size="11">{escape(label)}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def _model_scale_svg(rows: list[dict[str, str]], source: Path) -> str:
    model_sizes = sorted(
        {row.get("model_size", "") for row in rows if row.get("run_status") == "completed_training"}
    )
    if len(model_sizes) < 2:
        return _empty_svg(
            "Model scale comparison",
            "Only one model size has completed real-training rows in this phase.",
            source,
        )
    return _empty_svg(
        "Model scale comparison",
        "Real multi-scale comparison is intentionally deferred; no synthetic scaling curve drawn.",
        source,
    )


def _claim_boundary_svg(source: Path) -> str:
    lines = _svg_header(760, 170, "Claim support boundary", source, "scripts/generate_figures.py")
    lines.extend(
        [
            '<rect x="24" y="62" width="190" height="34" fill="#f2cf5b"/>',
            '<text x="38" y="84" font-family="Arial" font-size="13">Experiment candidate</text>',
            '<rect x="238" y="62" width="210" height="34" fill="#bab0ac"/>',
            '<text x="252" y="84" font-family="Arial" font-size="13">'
            "Preliminary trends only</text>",
            '<rect x="474" y="62" width="190" height="34" fill="#e45756"/>',
            '<text x="488" y="84" font-family="Arial" font-size="13">Not CCF-C ready</text>',
            "</svg>",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/figures")
    args = parser.parse_args()
    output_dir = root / args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    registry_path = root / "artifacts" / "runs" / "run_registry.csv"
    stats_main_path = root / "artifacts" / "stats" / "main_results.csv"
    ablation_path = root / "artifacts" / "tables" / "ablation_table.csv"

    registry_rows = _read_csv(registry_path)
    stats_rows = _read_csv(stats_main_path)
    ablation_rows = _read_csv(ablation_path)

    (output_dir / "baseline_retention.svg").write_text(
        _baseline_retention_svg(registry_rows, registry_path),
        encoding="utf-8",
    )
    (output_dir / "claim_support_boundary.svg").write_text(
        _claim_boundary_svg(registry_path),
        encoding="utf-8",
    )
    (output_dir / "seed_confidence_intervals.svg").write_text(
        _seed_ci_svg(stats_rows, stats_main_path),
        encoding="utf-8",
    )
    (output_dir / "ablation_effects.svg").write_text(
        _ablation_svg(ablation_rows, ablation_path),
        encoding="utf-8",
    )
    (output_dir / "privacy_utility_tradeoff.svg").write_text(
        _privacy_utility_svg(registry_rows, registry_path),
        encoding="utf-8",
    )
    (output_dir / "model_scale_comparison.svg").write_text(
        _model_scale_svg(registry_rows, registry_path),
        encoding="utf-8",
    )
    print(f"Figures generated: {output_dir}")


if __name__ == "__main__":
    main()
