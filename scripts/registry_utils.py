from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from experiment_utils import root

ALLOWED_RUN_STATUS = {
    "completed_training",
    "completed_filtering_only",
    "completed_smoke",
    "lightweight_dev",
    "failed_due_to_network",
    "failed_due_to_auth",
    "failed_due_to_disk",
    "failed_due_to_compute",
    "failed_due_to_timeout",
    "failed_due_to_environment",
    "configured_not_run",
    "dry_run_only",
    "incomplete",
}

ALLOWED_DATASET_STATUS = {
    "real_nonfallback",
    "real_local_nonfallback",
    "smoke_fixture",
    "synthetic",
    "fallback",
    "dataset_debug",
    "insufficient_streaming_sample",
    "failed_due_to_network",
    "failed_due_to_auth",
    "failed_due_to_disk",
    "failed_due_to_environment",
    "configured_not_run",
}

ALLOWED_DATASET_SCOPE = {
    "full_dataset",
    "official_split",
    "streaming_sample",
    "local_real_subset",
    "smoke_fixture",
    "synthetic_fixture",
    "configured_not_run",
}

REGISTRY_FIELDS = [
    "run_id",
    "timestamp_utc",
    "command",
    "config_path",
    "config_hash",
    "dataset_key",
    "dataset_status",
    "dataset_scope",
    "model_size",
    "model_config_path",
    "model_config_hash",
    "baseline_name",
    "seed",
    "train_steps",
    "train_tokens",
    "validation_tokens",
    "run_status",
    "failure_reason",
    "artifact_path",
    "artifact_hash",
    "environment_fingerprint_hash",
    "dataset_manifest_path",
    "metrics_path",
    "final_val_loss",
    "final_val_perplexity",
    "retention_rate",
    "tokenizer_type",
    "tokenizer_id",
    "tokenizer_hash",
    "vocab_size",
    "parameter_count",
    "evaluated_validation_tokens",
    "eval_batches",
    "eval_batch_size",
    "eval_block_size",
    "eval_token_budget",
    "eval_coverage_ratio",
    "final_train_loss",
    "final_validation_loss",
    "perplexity_or_proxy_perplexity",
    "model_quality_metric",
    "privacy_metric",
    "dedup_metric",
    "keep_rate",
]


def now_utc() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def stable_hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_hash(path: str | Path) -> str:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return ""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def config_hash(config_path: str | Path) -> str:
    path = Path(config_path)
    if not path.is_absolute():
        path = root / path
    return file_hash(path)


def relative(path: str | Path) -> str:
    file_path = Path(path)
    try:
        return file_path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return file_path.name


def environment_hash() -> str:
    fingerprint = root / "artifacts" / "environment" / "fingerprint.json"
    return file_hash(fingerprint)


def make_run_id(*parts: object) -> str:
    clean = [str(part).replace("\\", "/").replace(" ", "_") for part in parts]
    return ":".join(clean)


def sanitize_local_paths(value: str) -> str:
    """Remove machine-specific absolute paths before registry persistence."""
    sanitized = value
    root_variants = {
        str(root),
        root.as_posix(),
        str(root).replace("\\", "\\\\"),
        root.as_posix().replace("/", "\\"),
    }
    for variant in sorted(root_variants, key=len, reverse=True):
        if variant:
            sanitized = sanitized.replace(variant, "<repo_root>")
    sanitized = re.sub(
        r"[A-Za-z]:[\\/]+Users[\\/]+[^'\"\r\n,]+",
        "<local_user_path>",
        sanitized,
    )
    sanitized = re.sub(
        r"/(?:Users|home)/[^'\"\r\n,]+",
        "<local_user_path>",
        sanitized,
    )
    return sanitized


def normalize_record(record: dict[str, Any]) -> dict[str, str]:
    output = {field: "" for field in REGISTRY_FIELDS}
    output.update(
        {
            key: sanitize_local_paths(str(value))
            for key, value in record.items()
            if key in output
        }
    )
    output.setdefault("timestamp_utc", now_utc())
    if not output["timestamp_utc"]:
        output["timestamp_utc"] = now_utc()
    output["run_status"] = output["run_status"] or "incomplete"
    output["dataset_status"] = output["dataset_status"] or "configured_not_run"
    output["dataset_scope"] = output["dataset_scope"] or "configured_not_run"
    if output["run_status"] not in ALLOWED_RUN_STATUS:
        raise ValueError(f"Invalid run_status: {output['run_status']}")
    if output["dataset_status"] not in ALLOWED_DATASET_STATUS:
        raise ValueError(f"Invalid dataset_status: {output['dataset_status']}")
    if output["dataset_scope"] not in ALLOWED_DATASET_SCOPE:
        raise ValueError(f"Invalid dataset_scope: {output['dataset_scope']}")
    return output


def _legacy_to_schema(record: dict[str, Any]) -> dict[str, str]:
    dataset_key = str(record.get("dataset_key", ""))
    is_smoke = str(record.get("is_smoke", "")).casefold() == "true"
    used_fallback = str(record.get("used_fallback", "")).casefold() == "true"
    dataset_status = (
        "fallback"
        if used_fallback
        else "smoke_fixture"
        if is_smoke
        else "real_nonfallback"
    )
    dataset_scope = "smoke_fixture" if is_smoke or used_fallback else "official_split"
    legacy_status = str(record.get("run_status", "completed_filtering_only")).replace(
        "data_filter_only",
        "completed_filtering_only",
    )
    if legacy_status == "skipped":
        legacy_status = "incomplete"
    return normalize_record(
        {
            "run_id": record.get("run_id")
            or make_run_id(
                "legacy",
                dataset_key,
                record.get("baseline_name", ""),
                record.get("seed", ""),
            ),
            "timestamp_utc": record.get("timestamp_utc", "2026-06-04T00:00:00+00:00"),
            "command": record.get("command", "legacy_v4.5_registry_row"),
            "config_path": record.get("config_path", "configs/experiments/smoke.yaml"),
            "config_hash": record.get("config_hash", config_hash("configs/experiments/smoke.yaml")),
            "dataset_key": dataset_key,
            "dataset_status": dataset_status,
            "dataset_scope": dataset_scope,
            "model_size": record.get("model_size", ""),
            "model_config_path": record.get("model_config_path", ""),
            "model_config_hash": record.get("model_config_hash", ""),
            "baseline_name": record.get("baseline_name", ""),
            "seed": record.get("seed", ""),
            "train_steps": record.get("train_steps", "0"),
            "train_tokens": record.get("train_tokens", record.get("input_tokens", "0")),
            "validation_tokens": record.get("validation_tokens", "0"),
            "run_status": legacy_status,
            "failure_reason": record.get("failure_reason", ""),
            "artifact_path": record.get("artifact_path", record.get("artifact_dir", "")),
            "artifact_hash": record.get("artifact_hash", ""),
            "environment_fingerprint_hash": record.get(
                "environment_fingerprint_hash",
                environment_hash(),
            ),
            "dataset_manifest_path": record.get("dataset_manifest_path", ""),
            "metrics_path": record.get("metrics_path", ""),
            "final_val_loss": record.get("final_val_loss", ""),
            "final_val_perplexity": record.get("final_val_perplexity", ""),
            "retention_rate": record.get("retention_rate", ""),
        }
    )


def read_registry_jsonl() -> list[dict[str, str]]:
    path = root / "artifacts" / "runs" / "run_registry.jsonl"
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            rows.append(
                normalize_record(payload)
                if all(field in payload for field in REGISTRY_FIELDS)
                else _legacy_to_schema(payload)
            )
    return rows


def _raw_registry_payloads(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_registry_jsonl(rows: list[dict[str, str]]) -> None:
    path = root / "artifacts" / "runs" / "run_registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(normalize_record(row), sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )


def append_run(record: dict[str, Any]) -> dict[str, str]:
    path = root / "artifacts" / "runs" / "run_registry.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_record(record)
    if not normalized["run_id"]:
        normalized["run_id"] = make_run_id(
            normalized["timestamp_utc"],
            normalized["dataset_key"],
            normalized["model_size"],
            normalized["baseline_name"],
            normalized["run_status"],
        )
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(normalized, sort_keys=True) + "\n")
    rebuild_registry_csv()
    return normalized


def rebuild_registry_csv() -> list[dict[str, str]]:
    rows = read_registry_jsonl()
    csv_path = root / "artifacts" / "runs" / "run_registry.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summary = root / "artifacts" / "runs" / "run_summary.md"
    lines = [
        "# Run Registry Summary",
        "",
        "| Run ID | Dataset | Baseline | Model | Status | Dataset status | Train tokens |",
        "|---|---|---|---|---|---|---:|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['run_id']}` | {row['dataset_key']} | {row['baseline_name']} | "
            f"{row['model_size']} | {row['run_status']} | {row['dataset_status']} | "
            f"{row['train_tokens']} |"
        )
    summary.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows


def migrate_registry_to_schema() -> list[dict[str, str]]:
    path = root / "artifacts" / "runs" / "run_registry.jsonl"
    raw_rows = _raw_registry_payloads(path)
    needs_migration = any(
        any(field not in row for field in REGISTRY_FIELDS) for row in raw_rows
    )
    hash_before = file_hash(path)
    rows = read_registry_jsonl()
    if needs_migration:
        write_registry_jsonl(rows)
        log_path = root / "artifacts" / "runs" / "migration_log.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log = {
            "migration_time": now_utc(),
            "source_registry_path": "artifacts/runs/run_registry.jsonl",
            "target_registry_path": "artifacts/runs/run_registry.jsonl",
            "num_rows_before": len(raw_rows),
            "num_rows_after": len(rows),
            "reason": "Expand registry schema for tokenizer/evaluation/fairness fields.",
            "operator_script": "scripts/registry_utils.py",
            "preserved_run_ids": [row["run_id"] for row in rows],
            "hash_before": hash_before,
            "hash_after": file_hash(path),
        }
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(log, sort_keys=True) + "\n")
    rebuild_registry_csv()
    return rows
