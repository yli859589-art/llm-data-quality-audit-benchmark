from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import csv
import json
import random
from pathlib import Path

from experiment_utils import load_json_yaml, root
from registry_utils import (
    append_run,
    config_hash,
    environment_hash,
    file_hash,
    make_run_id,
    now_utc,
    relative,
)

from analysis.quality_error_analysis import (
    document_metrics,
    js_divergence,
    length_distribution,
    token_distribution,
)
from course_project_suite.llm_benchmark.dedup import exact_deduplicate
from course_project_suite.llm_benchmark.quality import filter_by_quality
from data.real_corpora import load_documents_from_config
from filters.hdqspp_v2 import config_from_mapping, select_hdqspp_v2


def _random_keep(documents: list[str], keep_rate: float, seed: int) -> list[str]:
    indexed = list(enumerate(documents))
    random.Random(seed).shuffle(indexed)
    keep = max(1, round(len(documents) * keep_rate))
    keep_indices = {index for index, _ in indexed[:keep]}
    return [document for index, document in enumerate(documents) if index in keep_indices]


def _select(
    method: str,
    train_documents: list[str],
    dev_documents: list[str],
    keep_rate: float,
) -> list[str]:
    if method == "hdqspp":
        selected, _ = filter_by_quality(train_documents, retention_ratio=keep_rate)
        return selected
    if method.startswith("v2_") or method == "hdqspp_v2":
        selected, _ = select_hdqspp_v2(
            train_documents,
            reference_documents=dev_documents,
            config=config_from_mapping(load_json_yaml("configs/filters/hdqspp_v2.yaml")),
            variant=method,
        )
        return selected
    if method == "random_same_keep_rate":
        return _random_keep(train_documents, keep_rate, 13)
    if method == "dedup_only":
        return exact_deduplicate(train_documents).documents
    raise ValueError(f"Unsupported method_debug candidate: {method}")


def _mean_proxy(documents: list[str], dev_tokens: object) -> float:
    metrics = [document_metrics(document, dev_tokens)["dev_loss_proxy"] for document in documents]
    return sum(metrics) / max(1, len(metrics))


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = sorted({field for row in rows for field in row})
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/method_debug.yaml")
    args = parser.parse_args()
    config = load_json_yaml(args.config)
    loaded = load_documents_from_config(root / config["dataset_config"], root=root)
    splits = loaded.metadata.get("predefined_splits")
    if not isinstance(splits, dict):
        raise SystemExit("method_debug requires predefined real WikiText-2 splits.")
    train_documents = list(splits["train"])
    dev_documents = list(splits["dev"])
    keep_rate = float(config.get("target_keep_rate", 0.6))
    candidates = list(config.get("candidate_methods", []))
    raw_token_dist = token_distribution(train_documents, top_k=5000)
    dev_token_dist = token_distribution(dev_documents, top_k=5000)
    raw_length_dist = length_distribution(train_documents)
    dev_length_dist = length_distribution(dev_documents)
    rows = []
    for method in candidates:
        selected = _select(str(method), train_documents, dev_documents, keep_rate)
        selected_token_dist = token_distribution(selected, top_k=5000)
        selected_length_dist = length_distribution(selected)
        rows.append(
            {
                "method": method,
                "run_status": "lightweight_dev",
                "dataset_key": loaded.dataset_key,
                "dataset_status": loaded.metadata.get("dataset_status"),
                "dataset_scope": loaded.metadata.get("dataset_scope"),
                "selected_documents": len(selected),
                "retention_rate": len(selected) / max(1, len(train_documents)),
                "token_js_vs_raw": js_divergence(selected_token_dist, raw_token_dist),
                "token_js_vs_dev": js_divergence(selected_token_dist, dev_token_dist),
                "length_js_vs_raw": js_divergence(selected_length_dist, raw_length_dist),
                "length_js_vs_dev": js_divergence(selected_length_dist, dev_length_dist),
                "dev_loss_proxy_mean": _mean_proxy(selected, dev_token_dist),
            }
        )
    output_dir = root / "artifacts" / "method_debug"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "method_debug_results.csv"
    json_path = output_dir / "method_debug_results.json"
    md_path = output_dir / "method_debug_summary.md"
    _write_csv(csv_path, rows)
    json_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(
        "# Method Debug Summary\n\n"
        "This is a proxy-only sandbox. It is excluded from main_results and "
        "does not support model-quality claims.\n\n"
        "| Method | Retention | Token JS vs raw | Length JS vs raw | Proxy loss |\n"
        "|---|---:|---:|---:|---:|\n"
        + "\n".join(
            f"| {row['method']} | {float(row['retention_rate']):.3f} | "
            f"{float(row['token_js_vs_raw']):.6f} | "
            f"{float(row['length_js_vs_raw']):.6f} | "
            f"{float(row['dev_loss_proxy_mean']):.4f} |"
            for row in rows
        )
        + "\n",
        encoding="utf-8",
    )
    record = append_run(
        {
            "run_id": make_run_id("method_debug", loaded.dataset_key, now_utc()),
            "timestamp_utc": now_utc(),
            "command": f"python scripts/run_method_debug.py --config {args.config}",
            "config_path": args.config,
            "config_hash": config_hash(args.config),
            "dataset_key": loaded.dataset_key,
            "dataset_status": str(loaded.metadata.get("dataset_status")),
            "dataset_scope": str(loaded.metadata.get("dataset_scope")),
            "model_size": "none",
            "model_config_path": "",
            "model_config_hash": "",
            "baseline_name": "method_debug",
            "seed": 13,
            "train_steps": 0,
            "train_tokens": 0,
            "validation_tokens": 0,
            "run_status": "lightweight_dev",
            "failure_reason": "",
            "artifact_path": relative(csv_path),
            "artifact_hash": file_hash(csv_path),
            "environment_fingerprint_hash": environment_hash(),
            "dataset_manifest_path": "artifacts/data/wikitext2_paper/data_manifest.json",
            "metrics_path": relative(json_path),
            "model_quality_metric": "proxy_only_not_model_quality",
        }
    )
    print(f"Method debug rows: {len(rows)}")
    print(f"Registry row: {record['run_id']}")


if __name__ == "__main__":
    main()
