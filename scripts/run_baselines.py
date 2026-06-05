from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
from dataclasses import asdict

from experiment_utils import load_json_yaml, rel, root
from registry_utils import (
    append_run,
    config_hash,
    environment_hash,
    file_hash,
    make_run_id,
    now_utc,
)

from baselines.data_quality_baselines import run_baseline, write_baseline_artifacts
from data.real_corpora import load_documents_from_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/smoke.yaml")
    args = parser.parse_args()
    config = load_json_yaml(args.config)
    baseline_names = list(config["baselines"])
    dataset_configs = config.get("dataset_configs") or [config["dataset_config"]]
    seeds = [int(seed) for seed in config.get("seeds", [13])]
    target_keep_rate = float(config.get("target_keep_rate", 0.6))
    rows: list[dict[str, object]] = []

    for dataset_config in dataset_configs:
        loaded = load_documents_from_config(root / dataset_config, root=root)
        dataset_output = root / "artifacts" / "baselines" / loaded.dataset_key
        for seed in seeds:
            for baseline_name in baseline_names:
                retained, result = run_baseline(
                    baseline_name,
                    loaded.documents,
                    target_keep_rate=target_keep_rate,
                    seed=seed,
                )
                baseline_output = dataset_output / baseline_name / f"seed_{seed}"
                write_baseline_artifacts(
                    output_dir=baseline_output.parent,
                    baseline_name=f"seed_{seed}",
                    documents=retained,
                    result=result,
                )
                metrics = asdict(result)
                status = "incomplete" if result.skipped else "completed_filtering_only"
                metrics_path = baseline_output / "metrics.json"
                dataset_status = loaded.metadata.get("dataset_status") or (
                    "fallback" if loaded.metadata.get("used_fallback") else "real_nonfallback"
                )
                dataset_scope = loaded.metadata.get("dataset_scope") or (
                    "smoke_fixture" if loaded.metadata.get("is_smoke") else "official_split"
                )
                record = append_run(
                    {
                        "run_id": make_run_id(
                            "filtering",
                            loaded.dataset_key,
                            baseline_name,
                            seed,
                            now_utc(),
                        ),
                        "timestamp_utc": now_utc(),
                        "command": f"python scripts/run_baselines.py --config {args.config}",
                        "config_path": args.config,
                        "config_hash": config_hash(args.config),
                        "dataset_key": loaded.dataset_key,
                        "dataset_status": dataset_status,
                        "dataset_scope": dataset_scope,
                        "model_size": "none",
                        "baseline_name": baseline_name,
                        "seed": seed,
                        "train_steps": 0,
                        "train_tokens": metrics["input_tokens"],
                        "validation_tokens": 0,
                        "evaluated_validation_tokens": 0,
                        "run_status": status,
                        "failure_reason": result.skip_reason,
                        "artifact_path": rel(metrics_path),
                        "artifact_hash": file_hash(metrics_path),
                        "environment_fingerprint_hash": environment_hash(),
                        "dataset_manifest_path": "",
                        "metrics_path": rel(metrics_path),
                        "retention_rate": metrics["retention_rate"],
                        "keep_rate": metrics["retention_rate"],
                        "model_quality_metric": "filtering_only",
                        "dedup_metric": metrics["removed_duplicates"],
                    }
                )
                rows.append(record)
    print(f"Baseline filtering rows appended: {len(rows)}")
    print(f"Registry: {root / 'artifacts' / 'runs' / 'run_registry.csv'}")


if __name__ == "__main__":
    main()
