from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

from experiment_utils import load_json_yaml, root
from registry_utils import read_registry_jsonl
from data.dataset_cards import write_dataset_card


DATASETS = [
    ("wikitext2_paper", "configs/data/wikitext2_paper.yaml"),
    ("openwebtext_streaming", "configs/data/openwebtext_streaming.yaml"),
    ("c4_en_streaming", "configs/data/c4_en_streaming.yaml"),
]
AUDIT_METHODS = {"raw", "random_same_keep_rate", "dedup_only", "hdqspp_v3"}
AUDIT_SEEDS = {"1", "2", "3"}
CROSS_FIELDS = [
    "dataset",
    "dataset_status",
    "dataset_scope",
    "method",
    "seed",
    "run_status",
    "train_tokens",
    "evaluated_validation_tokens",
    "tokenizer_hash",
    "vocab_size",
    "parameter_count",
    "mean_ppl",
    "final_validation_loss",
    "keep_rate",
    "distribution_shift_metric",
    "source_run_id",
    "artifact_hash",
    "safe_interpretation",
]
STATUS_FIELDS = [
    "dataset",
    "config_path",
    "manifest_path",
    "dataset_status",
    "dataset_scope",
    "is_streaming_sample",
    "is_full_dataset",
    "actual_documents",
    "actual_train_tokens",
    "actual_validation_tokens",
    "actual_test_tokens",
    "content_hash",
    "failure_reason",
    "completed_training_rows",
    "lightweight_dev_rows",
    "failed_rows",
]


def _read_manifest(dataset_key: str) -> tuple[dict[str, Any], str]:
    path = root / "artifacts" / "data" / dataset_key / "data_manifest.json"
    if not path.exists():
        return {}, ""
    return json.loads(path.read_text(encoding="utf-8")), path.relative_to(root).as_posix()


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _float(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key, "")
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(row: dict[str, Any], key: str) -> int:
    try:
        return int(float(row.get(key, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _safe_interpretation(row: dict[str, Any]) -> str:
    status = row.get("run_status", "")
    if status == "completed_training":
        return (
            "Completed under this dataset protocol; compare methods within the same dataset, "
            "tokenizer, vocabulary, parameter count, and token budget."
        )
    if status == "lightweight_dev":
        return "Lightweight development row only; do not use as a main cross-dataset result."
    if status.startswith("failed"):
        return "Failure is retained for audit evidence; do not treat as a completed run."
    return "Configured or incomplete row; status retained for audit transparency."


def _distribution_shift(row: dict[str, Any]) -> str:
    keep = _float(row, "keep_rate")
    if keep is None:
        keep = _float(row, "retention_rate")
    if keep is None:
        return ""
    return f"{abs(1.0 - keep):.6f}"


def _cross_row(row: dict[str, Any]) -> dict[str, Any]:
    ppl = row.get("final_val_perplexity") or row.get("perplexity_or_proxy_perplexity")
    return {
        "dataset": row.get("dataset_key", ""),
        "dataset_status": row.get("dataset_status", ""),
        "dataset_scope": row.get("dataset_scope", ""),
        "method": row.get("baseline_name", ""),
        "seed": row.get("seed", ""),
        "run_status": row.get("run_status", ""),
        "train_tokens": row.get("train_tokens", ""),
        "evaluated_validation_tokens": row.get("evaluated_validation_tokens", ""),
        "tokenizer_hash": row.get("tokenizer_hash", ""),
        "vocab_size": row.get("vocab_size", ""),
        "parameter_count": row.get("parameter_count", ""),
        "mean_ppl": ppl,
        "final_validation_loss": row.get("final_validation_loss") or row.get("final_val_loss", ""),
        "keep_rate": row.get("keep_rate") or row.get("retention_rate", ""),
        "distribution_shift_metric": _distribution_shift(row),
        "source_run_id": row.get("run_id", ""),
        "artifact_hash": row.get("artifact_hash", ""),
        "safe_interpretation": _safe_interpretation(row),
    }


def _placeholder_rows(
    *,
    dataset_key: str,
    manifest: dict[str, Any],
    config_path: str,
) -> list[dict[str, Any]]:
    status = manifest.get("dataset_status", "configured_not_run") if manifest else "configured_not_run"
    scope = manifest.get("dataset_scope", "configured_not_run") if manifest else "configured_not_run"
    rows = []
    for method in sorted(AUDIT_METHODS):
        rows.append(
            {
                "dataset": dataset_key,
                "dataset_status": status,
                "dataset_scope": scope,
                "method": method,
                "seed": "",
                "run_status": status if str(status).startswith("failed") else "configured_not_run",
                "safe_interpretation": (
                    f"No completed training row is available for {dataset_key}/{method}; "
                    f"see {config_path} and dataset_status_matrix."
                ),
            }
        )
    return rows


def generate() -> dict[str, Any]:
    output_dir = root / "artifacts" / "cross_dataset"
    output_dir.mkdir(parents=True, exist_ok=True)
    registry = read_registry_jsonl()
    cross_rows: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []

    latest_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in registry:
        if row.get("dataset_key") not in {dataset for dataset, _ in DATASETS}:
            continue
        if row.get("baseline_name") not in AUDIT_METHODS:
            continue
        if str(row.get("seed", "")) not in AUDIT_SEEDS:
            continue
        run_status = str(row.get("run_status", ""))
        if run_status not in {"completed_training", "lightweight_dev", "configured_not_run"} and not run_status.startswith("failed"):
            continue
        key = (row.get("dataset_key", ""), row.get("baseline_name", ""), row.get("seed", ""))
        latest_by_key[key] = row

    rows_by_dataset = {dataset: [] for dataset, _ in DATASETS}
    for row in latest_by_key.values():
        cross = _cross_row(row)
        cross_rows.append(cross)
        rows_by_dataset.setdefault(str(row.get("dataset_key", "")), []).append(cross)
        if str(row.get("run_status", "")).startswith("failed"):
            failure_rows.append(cross)

    for dataset_key, config_path in DATASETS:
        config = load_json_yaml(config_path) if (root / config_path).exists() else {}
        manifest, manifest_path = _read_manifest(dataset_key)
        if manifest:
            write_dataset_card(manifest, root / "artifacts" / "data" / dataset_key)
        dataset_rows = rows_by_dataset.get(dataset_key, [])
        if not dataset_rows:
            placeholder = _placeholder_rows(
                dataset_key=dataset_key,
                manifest=manifest,
                config_path=config_path,
            )
            cross_rows.extend(placeholder)
            dataset_rows = placeholder
        status_counts = Counter(row.get("run_status", "") for row in dataset_rows)
        status_row = {
            "dataset": dataset_key,
            "config_path": config_path,
            "manifest_path": manifest_path,
            "dataset_status": manifest.get("dataset_status", "configured_not_run"),
            "dataset_scope": manifest.get(
                "dataset_scope",
                "streaming_sample" if config.get("streaming") else "configured_not_run",
            ),
            "is_streaming_sample": manifest.get("is_streaming_sample", bool(config.get("streaming"))),
            "is_full_dataset": manifest.get("is_full_dataset", False),
            "actual_documents": manifest.get("actual_documents", ""),
            "actual_train_tokens": manifest.get("actual_train_tokens", ""),
            "actual_validation_tokens": manifest.get("actual_validation_tokens", ""),
            "actual_test_tokens": manifest.get("actual_test_tokens", ""),
            "content_hash": manifest.get("content_hash", manifest.get("corpus_sha256", "")),
            "failure_reason": manifest.get("failure_reason", ""),
            "completed_training_rows": status_counts.get("completed_training", 0),
            "lightweight_dev_rows": status_counts.get("lightweight_dev", 0),
            "failed_rows": sum(count for status, count in status_counts.items() if str(status).startswith("failed")),
        }
        status_rows.append(status_row)
        if status_row["failure_reason"]:
            failure_rows.append(
                {
                    "dataset": dataset_key,
                    "dataset_status": status_row["dataset_status"],
                    "dataset_scope": status_row["dataset_scope"],
                    "method": "data_prepare",
                    "run_status": status_row["dataset_status"],
                    "safe_interpretation": status_row["failure_reason"],
                }
            )

    cross_rows = sorted(
        cross_rows,
        key=lambda row: (
            str(row.get("dataset", "")),
            str(row.get("method", "")),
            str(row.get("seed", "")),
            str(row.get("run_status", "")),
        ),
    )
    _write_csv(output_dir / "cross_dataset_results.csv", cross_rows, CROSS_FIELDS)
    _write_csv(output_dir / "dataset_status_matrix.csv", status_rows, STATUS_FIELDS)
    _write_csv(output_dir / "cross_dataset_failures.csv", failure_rows, CROSS_FIELDS)
    (output_dir / "cross_dataset_results.json").write_text(
        json.dumps(cross_rows, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    completed = [row for row in cross_rows if row.get("run_status") == "completed_training"]
    completed_by_dataset = Counter(row.get("dataset", "") for row in completed)
    means = []
    for dataset in sorted({row.get("dataset", "") for row in completed}):
        for method in sorted(AUDIT_METHODS):
            values = [
                _float(row, "mean_ppl")
                for row in completed
                if row.get("dataset") == dataset and row.get("method") == method
            ]
            clean = [value for value in values if value is not None]
            if clean:
                means.append(f"- `{dataset}` / `{method}` mean PPL: `{mean(clean):.4f}`")
    summary = [
        "# Cross-Dataset Audit Summary",
        "",
        "This artifact separates completed, lightweight, failed, and configured-only rows.",
        "Streaming samples are bounded samples, not complete upstream corpora.",
        "",
        "## Dataset Status",
        "",
        "| Dataset | Status | Scope | Completed rows | Failed rows | Failure reason |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in status_rows:
        summary.append(
            f"| {row['dataset']} | `{row['dataset_status']}` | `{row['dataset_scope']}` | "
            f"{row['completed_training_rows']} | {row['failed_rows']} | {row['failure_reason']} |"
        )
    summary.extend(["", "## Completed Training Means", ""])
    summary.extend(means or ["- No cross-dataset completed-training rows beyond current registry evidence."])
    summary.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "- Do not compare perplexity across datasets unless tokenizer hash, vocabulary size, parameter count, and token budget match.",
            "- Failed datasets remain visible in `dataset_status_matrix.csv` and `cross_dataset_failures.csv`.",
            "- This is an audit benchmark expansion, not a supported over-raw method claim.",
        ]
    )
    (output_dir / "cross_dataset_summary.md").write_text(
        "\n".join(summary) + "\n",
        encoding="utf-8",
    )
    return {
        "cross_rows": cross_rows,
        "status_rows": status_rows,
        "failure_rows": failure_rows,
        "completed_by_dataset": dict(completed_by_dataset),
    }


def main() -> None:
    result = generate()
    print(f"Cross-dataset rows: {len(result['cross_rows'])}")
    print(f"Dataset status rows: {len(result['status_rows'])}")
    print(f"Failure rows: {len(result['failure_rows'])}")


if __name__ == "__main__":
    main()
