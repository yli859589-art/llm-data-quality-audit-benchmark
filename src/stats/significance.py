from __future__ import annotations

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def _portable_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.name


def _read_registry(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _numeric(row: dict[str, str], field: str) -> float | None:
    try:
        value = row.get(field, "")
        return float(value) if value not in {"", "NA", "nan"} else None
    except ValueError:
        return None


def _bootstrap_ci(values: list[float], *, seed: int = 13) -> tuple[float | None, float | None]:
    if len(values) < 2:
        return None, None
    rng = random.Random(seed)
    means = []
    for _ in range(500):
        sample = [rng.choice(values) for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    low = means[int(0.025 * len(means))]
    high = means[int(0.975 * len(means)) - 1]
    return low, high


def _claim_status(values: list[float], ci_low: float | None, ci_high: float | None) -> str:
    if len(values) < 3:
        return "unsupported_seed_count"
    if ci_low is None or ci_high is None:
        return "unsupported_missing_ci"
    if ci_low <= 0 <= ci_high:
        return "trend_only_ci_crosses_zero"
    return "supported_by_registry_metric"


def analyze_registry(input_path: Path, output_dir: Path) -> dict[str, Any]:
    rows = _read_registry(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("dataset_key", ""), row.get("baseline_name", ""))].append(row)

    summaries = []
    for (dataset_key, baseline_name), group_rows in grouped.items():
        retention_values = [
            value for row in group_rows if (value := _numeric(row, "retention_rate")) is not None
        ]
        mean_retention = (
            sum(retention_values) / len(retention_values) if retention_values else math.nan
        )
        ci_low, ci_high = _bootstrap_ci(retention_values)
        summaries.append(
            {
                "dataset_key": dataset_key,
                "baseline_name": baseline_name,
                "rows": len(group_rows),
                "metric": "retention_rate",
                "mean": mean_retention,
                "ci95_low": ci_low,
                "ci95_high": ci_high,
                "claim_status": _claim_status(retention_values, ci_low, ci_high),
            }
        )

    main_csv = output_dir / "main_results.csv"
    with main_csv.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "dataset_key",
            "baseline_name",
            "rows",
            "metric",
            "mean",
            "ci95_low",
            "ci95_high",
            "claim_status",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)

    tests = {
        "input_registry": _portable_path(input_path),
        "rows": len(rows),
        "tests": summaries,
        "hard_boundary": (
            "Retention-rate summaries are not model-quality significance tests. "
            "Perplexity or validation-loss claims require completed multi-seed model runs."
        ),
    }
    (output_dir / "significance_tests.json").write_text(
        json.dumps(tests, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "main_results.tex").write_text(
        "\\begin{tabular}{llrr}\nDataset & Baseline & Rows & Mean retention \\\\\n"
        + "\n".join(
            f"{row['dataset_key']} & {row['baseline_name']} & {row['rows']} & "
            f"{row['mean']:.3f} \\\\" if not math.isnan(row["mean"]) else
            f"{row['dataset_key']} & {row['baseline_name']} & {row['rows']} & NA \\\\"
            for row in summaries
        )
        + "\n\\end{tabular}\n",
        encoding="utf-8",
    )
    unsupported = [row for row in summaries if not row["claim_status"].startswith("supported")]
    report_lines = [
        "# Claim Safety Report",
        "",
        f"- Registry rows analyzed: {len(rows)}",
        f"- Unsupported or trend-only rows: {len(unsupported)}",
        "- Model-quality improvement claims remain unsupported until real multi-seed "
        "validation/perplexity runs are present.",
    ]
    (output_dir / "claim_safety_report.md").write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )
    return {"summaries": summaries, "unsupported": unsupported}
