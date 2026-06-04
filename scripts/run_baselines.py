from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict

from experiment_utils import load_json_yaml, rel, root

from baselines.data_quality_baselines import run_baseline, write_baseline_artifacts
from data.real_corpora import load_documents_from_config

REGISTRY_FIELDS = [
    "run_id",
    "experiment_key",
    "mode",
    "dataset_key",
    "baseline_name",
    "seed",
    "run_status",
    "is_smoke",
    "used_fallback",
    "input_documents",
    "output_documents",
    "retention_rate",
    "input_tokens",
    "output_tokens",
    "pii_hits_before",
    "pii_hits_after",
    "removed_duplicates",
    "model_quality_metric",
    "artifact_dir",
]


def _write_registry(rows: list[dict[str, object]]) -> None:
    registry_csv = root / "artifacts" / "runs" / "run_registry.csv"
    registry_jsonl = root / "artifacts" / "runs" / "run_registry.jsonl"
    registry_md = root / "artifacts" / "runs" / "run_summary.md"
    registry_csv.parent.mkdir(parents=True, exist_ok=True)
    with registry_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REGISTRY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    registry_jsonl.write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# Run Registry Summary",
        "",
        "| Dataset | Baseline | Seed | Status | Retention | Fallback |",
        "|---|---|---:|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['dataset_key']} | {row['baseline_name']} | {row['seed']} | "
            f"{row['run_status']} | {float(row['retention_rate']):.3f} | "
            f"{row['used_fallback']} |"
        )
    registry_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
                status = "skipped" if result.skipped else "data_filter_only"
                rows.append(
                    {
                        "run_id": (
                            f"{config['experiment_key']}:{loaded.dataset_key}:"
                            f"{baseline_name}:seed{seed}"
                        ),
                        "experiment_key": config["experiment_key"],
                        "mode": config["mode"],
                        "dataset_key": loaded.dataset_key,
                        "baseline_name": baseline_name,
                        "seed": seed,
                        "run_status": status,
                        "is_smoke": loaded.metadata.get("is_smoke", False),
                        "used_fallback": loaded.metadata.get("used_fallback", False),
                        "input_documents": metrics["input_documents"],
                        "output_documents": metrics["output_documents"],
                        "retention_rate": metrics["retention_rate"],
                        "input_tokens": metrics["input_tokens"],
                        "output_tokens": metrics["output_tokens"],
                        "pii_hits_before": metrics["pii_hits_before"],
                        "pii_hits_after": metrics["pii_hits_after"],
                        "removed_duplicates": metrics["removed_duplicates"],
                        "model_quality_metric": "NA",
                        "artifact_dir": rel(baseline_output),
                    }
                )
    _write_registry(rows)
    print(f"Baseline registry rows: {len(rows)}")
    print(f"Registry: {root / 'artifacts' / 'runs' / 'run_registry.csv'}")


if __name__ == "__main__":
    main()
