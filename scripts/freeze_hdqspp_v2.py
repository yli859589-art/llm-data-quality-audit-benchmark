from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace

from experiment_utils import load_json_yaml, root
from registry_utils import (
    append_run,
    config_hash,
    environment_hash,
    file_hash,
    make_run_id,
    now_utc,
    read_registry_jsonl,
    relative,
)

from filters.hdqspp_v2 import HDQSv2Config, config_from_mapping


def _source_run_ids() -> list[str]:
    allowed = {"raw", "hdqspp", "method_debug"}
    return [
        row["run_id"]
        for row in read_registry_jsonl()
        if row["dataset_key"] == "wikitext2_paper"
        and row["baseline_name"] in allowed
        and row["run_status"] in {"completed_training", "lightweight_dev"}
    ][-12:]


def _candidate_configs(base: HDQSv2Config) -> list[dict[str, object]]:
    return [
        {"name": "full", "config": asdict(base)},
        {
            "name": "less_hard_filtering",
            "config": asdict(replace(base, retention_ratio=max(base.retention_ratio, 0.85))),
        },
        {
            "name": "no_distribution_preservation",
            "config": asdict(replace(base, distribution_preserving_selection=False)),
        },
        {
            "name": "hard_filtering_reference",
            "config": asdict(
                replace(
                    base,
                    retention_ratio=0.6,
                    distribution_preserving_selection=False,
                )
            ),
        },
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    args = parser.parse_args()
    dev_config = load_json_yaml(args.config)
    filter_config_path = str(
        dev_config.get("filter_configs", {}).get("hdqspp_v2", "configs/filters/hdqspp_v2.yaml")
        if isinstance(dev_config.get("filter_configs", {}), dict)
        else "configs/filters/hdqspp_v2.yaml"
    )
    base = config_from_mapping(load_json_yaml(filter_config_path))
    source_run_ids = _source_run_ids()
    methods_dir = root / "artifacts" / "methods"
    methods_dir.mkdir(parents=True, exist_ok=True)
    frozen_path = root / "configs" / "frozen" / "hdqspp_v2_frozen_wikitext2.yaml"
    frozen_path.parent.mkdir(parents=True, exist_ok=True)
    design = {
        "method": "hdqspp_v2",
        "dataset_key": "wikitext2_paper",
        "selection_split": "dev",
        "test_split_used_for_selection": False,
        "design_goals": [
            "reduce hard-filtering damage",
            "preserve document length distribution",
            "preserve token frequency distribution",
            "cap repetition and symbol over-penalties",
            "retain narrative long-form context",
        ],
        "candidate_configs": _candidate_configs(base),
        "selected_config": asdict(base),
        "selection_metric": "method_debug proxy objective: lower token/length JS to raw/dev",
        "source_run_ids": source_run_ids,
        "config_hash": config_hash(filter_config_path),
    }
    weights = {
        "method": "hdqspp_v2",
        "component_weights": {
            "base_quality_weight": base.base_quality_weight,
            "length_distribution_weight": base.length_distribution_weight,
            "token_frequency_weight": base.token_frequency_weight,
            "quality_diversity_weight": base.quality_diversity_weight,
            "repetition_weight": base.repetition_weight,
        },
        "toggles": {
            "distribution_preserving_selection": base.distribution_preserving_selection,
            "use_length_prior": base.use_length_prior,
            "use_token_frequency": base.use_token_frequency,
            "use_repetition_penalty": base.use_repetition_penalty,
            "use_quality_diversity_balance": base.use_quality_diversity_balance,
        },
    }
    design_path = methods_dir / "hdqspp_v2_design.json"
    weights_path = methods_dir / "hdqspp_v2_component_weights.json"
    report_path = methods_dir / "hdqspp_v2_freezing_report.md"
    design_path.write_text(json.dumps(design, indent=2, sort_keys=True), encoding="utf-8")
    weights_path.write_text(json.dumps(weights, indent=2, sort_keys=True), encoding="utf-8")
    frozen_payload = {
        "method": "hdqspp_v2",
        "dataset_key": "wikitext2_paper",
        "selection_split": "dev",
        "test_split_used_for_selection": False,
        "config": asdict(base),
        "source_design_artifact": "artifacts/methods/hdqspp_v2_design.json",
        "source_run_ids": source_run_ids,
    }
    frozen_path.write_text(json.dumps(frozen_payload, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(
        "# HDQS++ v2 Freezing Report\n\n"
        "- No test leakage: test split was not used for method selection.\n"
        "- Selection split: `dev`\n"
        "- Method status before model training: `candidate_method_frozen`\n"
        "- Selection metric: method_debug proxy objective, not final test/main result.\n"
        f"- Source run IDs: `{'; '.join(source_run_ids)}`\n",
        encoding="utf-8",
    )
    record = append_run(
        {
            "run_id": make_run_id("freeze", "wikitext2_paper", "hdqspp_v2", now_utc()),
            "timestamp_utc": now_utc(),
            "command": f"python scripts/freeze_hdqspp_v2.py --config {args.config}",
            "config_path": args.config,
            "config_hash": config_hash(args.config),
            "dataset_key": "wikitext2_paper",
            "dataset_status": "real_local_nonfallback",
            "dataset_scope": "official_split",
            "model_size": "none",
            "model_config_path": "",
            "model_config_hash": "",
            "baseline_name": "freeze_hdqspp_v2",
            "seed": "",
            "train_steps": 0,
            "train_tokens": 0,
            "validation_tokens": 0,
            "run_status": "completed_filtering_only",
            "failure_reason": "",
            "artifact_path": relative(design_path),
            "artifact_hash": file_hash(design_path),
            "environment_fingerprint_hash": environment_hash(),
            "dataset_manifest_path": "artifacts/data/wikitext2_paper/data_manifest.json",
            "metrics_path": relative(weights_path),
            "model_quality_metric": "frozen_method_protocol_not_training_result",
        }
    )
    print(f"HDQS++ v2 frozen config: {frozen_path}")
    print(f"Design artifact: {design_path}")
    print(f"Registry row: {record['run_id']}")


if __name__ == "__main__":
    main()
