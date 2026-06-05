from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import csv
import json
from pathlib import Path

from experiment_utils import root
from registry_utils import REGISTRY_FIELDS, migrate_registry_to_schema

OFFICIAL_MAIN_BASELINES = {
    "raw",
    "random_same_keep_rate",
    "length_filter",
    "dedup_only",
    "hdqspp",
    "hdqspp_v2",
    "hdqspp_v2_no_token_frequency",
    "hdqspp_v3",
    "calibrated_quality_scorer",
}


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
    registry = migrate_registry_to_schema()
    if not registry:
        registry = _read_csv(root / "artifacts" / "runs" / "run_registry.csv")

    def write_rows(name: str, rows: list[dict[str, str]]) -> None:
        path = output_dir / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    candidate_main_rows = [
        row
        for row in registry
        if row["run_status"] == "completed_training"
        and row["baseline_name"] in OFFICIAL_MAIN_BASELINES
        and row["dataset_status"] in {"real_nonfallback", "real_local_nonfallback"}
        and row["dataset_scope"] in {"official_split", "full_dataset", "local_real_subset"}
        and int(row.get("train_tokens") or 0) >= 1_000_000
        and int(row.get("evaluated_validation_tokens") or 0) >= 50_000
        and row.get("tokenizer_hash")
        and row.get("vocab_size")
        and row.get("parameter_count")
    ]
    latest_main_rows: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in candidate_main_rows:
        key = (row["dataset_key"], row["model_size"], row["baseline_name"], row["seed"])
        latest_main_rows[key] = row
    main_rows = list(latest_main_rows.values())
    filtering_rows = [
        row for row in registry if row["run_status"] == "completed_filtering_only"
    ]
    smoke_rows = [
        row
        for row in registry
        if row["dataset_status"] in {"smoke_fixture", "synthetic", "fallback"}
        or row["run_status"] == "completed_smoke"
    ]
    lightweight_rows = [row for row in registry if row["run_status"] == "lightweight_dev"]
    training_rows = [
        row
        for row in registry
        if row["run_status"] in {"completed_training", "lightweight_dev"}
    ]
    write_rows("main_results.csv", main_rows)
    write_rows("filtering_results.csv", filtering_rows)
    write_rows("smoke_results.csv", smoke_rows)
    write_rows("lightweight_dev_results.csv", lightweight_rows)
    write_rows("model_training_results.csv", training_rows)

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
        retention = row.get("retention_rate") or "0"
        lines.append(
            f"| {row['dataset_key']} | {row['baseline_name']} | {row['seed']} | "
            f"{float(retention):.3f} | {row['dataset_status']} | "
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
        baseline = row.get("baseline_name") or row.get("baseline") or row.get("comparison", "")
        rows_count = row.get("rows") or row.get("n_paired_seeds", "")
        claim_status = row.get("claim_status") or row.get("status", "")
        stats_lines.append(
            f"| {row.get('dataset_key', '')} | {baseline} | {rows_count} | "
            f"{claim_status} |"
        )
    (output_dir / "significance_summary.md").write_text(
        "\n".join(stats_lines) + "\n",
        encoding="utf-8",
    )
    print(f"Tables generated: {output_dir}")


if __name__ == "__main__":
    main()
