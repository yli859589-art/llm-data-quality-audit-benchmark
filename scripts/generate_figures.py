from __future__ import annotations

import argparse
import csv
from pathlib import Path

from experiment_utils import root


def _read_registry(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _bar_svg(rows: list[dict[str, str]]) -> str:
    unique = []
    seen = set()
    for row in rows:
        key = (row["dataset_key"], row["baseline_name"])
        if key not in seen and row["run_status"] != "skipped":
            seen.add(key)
            unique.append(row)
    width = 900
    height = max(220, 40 + 24 * len(unique))
    labels_width = 250
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="20" y="24" font-family="Arial" font-size="16">'
        "Baseline retention rates</text>",
    ]
    for index, row in enumerate(unique):
        y = 52 + index * 24
        retention = float(row["retention_rate"])
        bar_width = int(retention * 500)
        label = f"{row['dataset_key']} / {row['baseline_name']}"
        lines.append(
            f'<text x="20" y="{y + 14}" font-family="Arial" font-size="11">{label}</text>'
        )
        lines.append(
            f'<rect x="{labels_width}" y="{y}" width="{bar_width}" height="16" '
            'fill="#4c78a8"/>'
        )
        lines.append(
            f'<text x="{labels_width + bar_width + 8}" y="{y + 13}" '
            f'font-family="Arial" font-size="11">{retention:.2f}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/figures")
    args = parser.parse_args()
    output_dir = root / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = _read_registry(root / "artifacts" / "runs" / "run_registry.csv")
    (output_dir / "baseline_retention.svg").write_text(_bar_svg(rows), encoding="utf-8")
    status_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="160">\n'
        '<rect width="100%" height="100%" fill="white"/>\n'
        '<text x="24" y="36" font-family="Arial" font-size="18">'
        "Claim support boundary</text>\n"
        '<rect x="24" y="60" width="180" height="32" fill="#f2cf5b"/>\n'
        '<text x="36" y="82" font-family="Arial" font-size="13">'
        "Engineering prototype</text>\n"
        '<rect x="230" y="60" width="180" height="32" fill="#bab0ac"/>\n'
        '<text x="242" y="82" font-family="Arial" font-size="13">'
        "Paper claims pending</text>\n"
        '<rect x="436" y="60" width="180" height="32" fill="#e45756"/>\n'
        '<text x="448" y="82" font-family="Arial" font-size="13">'
        "Not CCF-C ready</text>\n"
        "</svg>\n"
    )
    (output_dir / "claim_support_boundary.svg").write_text(status_svg, encoding="utf-8")
    print(f"Figures generated: {output_dir}")


if __name__ == "__main__":
    main()
