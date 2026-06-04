from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from experiment_utils import root


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/tables")
    args = parser.parse_args()
    output_dir = root / args.output
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = _read_csv(root / "artifacts" / "runs" / "run_registry.csv")
    lines = [
        "# Baseline Comparison",
        "",
        "Mode: smoke/dev registry consolidation",
        "Seed setting: recorded per row",
        "Training budget: data-filter-only rows do not train a model",
        "Interpretation: supports engineering readiness, not paper-level model claims",
        "",
        "| Dataset | Baseline | Seed | Retention | Fallback | Status |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in registry:
        lines.append(
            f"| {row['dataset_key']} | {row['baseline_name']} | {row['seed']} | "
            f"{float(row['retention_rate']):.3f} | {row['used_fallback']} | "
            f"{row['run_status']} |"
        )
    (output_dir / "baseline_comparison.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    stats_path = root / "artifacts" / "stats" / "significance_tests.json"
    stats = json.loads(stats_path.read_text(encoding="utf-8")) if stats_path.exists() else {}
    stats_lines = [
        "# Significance Summary",
        "",
        "Mode: registry audit",
        "Seed setting: requires at least three seeds for supported claims",
        "Training budget: model-training metrics are absent unless explicitly recorded",
        "Interpretation: unsupported rows are claim-safety warnings",
        "",
        "| Dataset | Baseline | Rows | Claim status |",
        "|---|---|---:|---|",
    ]
    for row in stats.get("tests", []):
        stats_lines.append(
            f"| {row['dataset_key']} | {row['baseline_name']} | {row['rows']} | "
            f"{row['claim_status']} |"
        )
    (output_dir / "significance_summary.md").write_text(
        "\n".join(stats_lines) + "\n",
        encoding="utf-8",
    )
    print(f"Tables generated: {output_dir}")


if __name__ == "__main__":
    main()
