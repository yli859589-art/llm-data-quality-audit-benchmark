from __future__ import annotations

import csv
import json
from html import escape
from pathlib import Path

from experiment_utils import load_json_yaml, root

from data.real_corpora import load_documents_from_config
from diagnostics.hdqspp_failure import summarize_hdqspp_failure
from filters.hdqspp_v2 import config_from_mapping


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({field for row in rows for field in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _histogram_svg(rows: list[dict[str, object]], output: Path) -> None:
    bins = [i / 20 for i in range(21)]
    kept = [0] * 20
    dropped = [0] * 20
    for row in rows:
        score = float(row["hdqspp_score"])
        index = min(19, max(0, int(score * 20)))
        if row["kept_by_hdqspp"] == "True" or row["kept_by_hdqspp"] is True:
            kept[index] += 1
        else:
            dropped[index] += 1
    max_count = max(kept + dropped + [1])
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320">',
        "<desc>source=artifacts/diagnostics/hdqspp_failure_analysis.csv</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="32" font-family="Arial" font-size="18">HDQS++ score distribution</text>',
    ]
    for i in range(20):
        x = 60 + i * 39
        kept_h = 220 * kept[i] / max_count
        dropped_h = 220 * dropped[i] / max_count
        lines.append(
            f'<rect x="{x}" y="{280 - kept_h:.1f}" width="16" '
            f'height="{kept_h:.1f}" fill="#4c78a8"/>'
        )
        lines.append(
            f'<rect x="{x + 17}" y="{280 - dropped_h:.1f}" width="16" '
            f'height="{dropped_h:.1f}" fill="#e45756"/>'
        )
    lines.append(f'<text x="60" y="305" font-family="Arial" font-size="11">{bins[0]:.2f}</text>')
    lines.append(f'<text x="800" y="305" font-family="Arial" font-size="11">{bins[-1]:.2f}</text>')
    lines.append("</svg>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _scatter_svg(rows: list[dict[str, object]], output: Path) -> None:
    sample = rows[:: max(1, len(rows) // 220)]
    scores = [float(row["hdqspp_score"]) for row in sample]
    losses = [float(row["dev_loss_proxy"]) for row in sample]
    min_loss, max_loss = min(losses), max(losses)
    span = max(max_loss - min_loss, 1e-9)
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="420">',
        "<desc>source=artifacts/diagnostics/hdqspp_failure_analysis.csv</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="32" font-family="Arial" font-size="18">'
        "Quality score vs dev unigram loss proxy</text>",
        '<line x1="70" y1="360" x2="840" y2="360" stroke="#333"/>',
        '<line x1="70" y1="60" x2="70" y2="360" stroke="#333"/>',
    ]
    for score, loss in zip(scores, losses, strict=False):
        x = 70 + score * 760
        y = 360 - ((loss - min_loss) / span) * 300
        lines.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#4c78a8" opacity="0.55"/>')
    lines.append("</svg>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _examples_svg(summary: dict[str, object], output: Path) -> None:
    dropped = summary["top_dropped_examples"][:4]
    kept = summary["top_kept_low_quality_examples"][:4]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="520">',
        "<desc>source=artifacts/diagnostics/hdqspp_failure_analysis.json</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="32" font-family="Arial" font-size="18">Kept vs dropped examples</text>',
        '<text x="24" y="66" font-family="Arial" font-size="14">'
        "Top dropped low proxy-loss examples</text>",
        '<text x="570" y="66" font-family="Arial" font-size="14">'
        "Top kept low HDQS++ score examples</text>",
    ]
    for i, row in enumerate(dropped):
        y = 96 + i * 88
        lines.append(
            f'<text x="24" y="{y}" font-family="Arial" font-size="11">'
            f'{escape(str(row["excerpt"]))}</text>'
        )
    for i, row in enumerate(kept):
        y = 96 + i * 88
        lines.append(
            f'<text x="570" y="{y}" font-family="Arial" font-size="11">'
            f'{escape(str(row["excerpt"]))}</text>'
        )
    lines.append("</svg>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _keep_rate_svg(summary: dict[str, object], output: Path) -> None:
    values = [
        ("raw", float(summary["raw_keep_rate"])),
        ("random_same_keep_rate", float(summary["random_same_keep_rate"])),
        ("hdqspp", float(summary["hdqspp_keep_rate"])),
        ("hdqspp_v2", float(summary["hdqspp_v2_keep_rate"])),
    ]
    lines = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="820" height="280">',
        "<desc>source=artifacts/diagnostics/hdqspp_failure_analysis.json</desc>",
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="24" y="32" font-family="Arial" font-size="18">'
        "Baseline keep-rate comparison</text>",
    ]
    for i, (name, value) in enumerate(values):
        y = 70 + i * 42
        width = value * 560
        lines.append(f'<text x="24" y="{y + 15}" font-family="Arial" font-size="12">{name}</text>')
        lines.append(f'<rect x="210" y="{y}" width="{width:.1f}" height="24" fill="#4c78a8"/>')
        lines.append(
            f'<text x="{220 + width:.1f}" y="{y + 16}" '
            f'font-family="Arial" font-size="12">{value:.3f}</text>'
        )
    lines.append("</svg>")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    config = load_json_yaml("configs/experiments/dev.yaml")
    loaded = load_documents_from_config(root / config["dataset_config"], root=root)
    splits = loaded.metadata.get("predefined_splits")
    if not isinstance(splits, dict):
        raise SystemExit("HDQS++ diagnostics require predefined WikiText-2 splits.")
    v2_config = config_from_mapping(load_json_yaml("configs/filters/hdqspp_v2.yaml"))
    rows, summary = summarize_hdqspp_failure(
        list(splits["train"]),
        list(splits["dev"]),
        list(splits["test"]),
        retention_ratio=float(config.get("target_keep_rate", 0.6)),
        v2_config=v2_config,
    )
    output_dir = root / "artifacts" / "diagnostics"
    figure_dir = root / "artifacts" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    figure_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "hdqspp_failure_analysis.csv"
    json_path = output_dir / "hdqspp_failure_analysis.json"
    md_path = output_dir / "hdqspp_failure_analysis.md"
    _write_csv(csv_path, rows)
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# HDQS++ Failure Analysis",
                "",
                f"- HDQS++ keep rate: `{summary['hdqspp_keep_rate']:.3f}`",
                f"- HDQS++ v2 keep rate: `{summary['hdqspp_v2_keep_rate']:.3f}`",
                f"- Token JS HDQS++ vs raw: `{summary['token_js_hdqspp_vs_raw']:.6f}`",
                f"- Token JS HDQS++ v2 vs raw: `{summary['token_js_hdqspp_v2_vs_raw']:.6f}`",
                f"- Length JS HDQS++ vs raw: `{summary['length_js_hdqspp_vs_raw']:.6f}`",
                f"- Length JS HDQS++ v2 vs raw: `{summary['length_js_hdqspp_v2_vs_raw']:.6f}`",
                "",
                "Diagnosis: v1 is a hard 60% filter and shifts length/token distribution. "
                "v2 is designed to preserve distribution and reduce over-penalization.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    _histogram_svg(rows, figure_dir / "hdqspp_score_distribution.svg")
    _scatter_svg(rows, figure_dir / "quality_vs_loss_proxy.svg")
    _examples_svg(summary, figure_dir / "kept_vs_dropped_examples.svg")
    _keep_rate_svg(summary, figure_dir / "baseline_keep_rate_comparison.svg")
    print(f"HDQS++ diagnostics rows: {len(rows)}")
    print(f"Diagnostic report: {md_path}")


if __name__ == "__main__":
    main()
