from __future__ import annotations

import argparse
import json
from dataclasses import asdict

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

from filters.hdqspp_v3 import config_from_mapping


def _source_run_ids() -> list[str]:
    allowed = {
        "raw",
        "random_same_keep_rate",
        "dedup_only",
        "hdqspp",
        "hdqspp_v2",
        "ablation_v2_without_token_frequency_preservation",
        "ablation_v2_without_distribution_preservation",
        "ablation_v2_without_length_prior",
    }
    rows = [
        row
        for row in read_registry_jsonl()
        if row.get("dataset_key") == "wikitext2_paper"
        and row.get("baseline_name") in allowed
        and row.get("run_status") in {"completed_training", "lightweight_dev"}
    ]
    return [row["run_id"] for row in rows[-18:]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    args = parser.parse_args()
    dev_config = load_json_yaml(args.config)
    filter_configs = dev_config.get("filter_configs", {})
    if not isinstance(filter_configs, dict):
        filter_configs = {}
    config_path = str(filter_configs.get("hdqspp_v3", "configs/filters/hdqspp_v3.yaml"))
    base = config_from_mapping(load_json_yaml(config_path))
    source_run_ids = _source_run_ids()
    methods_dir = root / "artifacts" / "methods"
    methods_dir.mkdir(parents=True, exist_ok=True)
    frozen_path = root / "configs" / "frozen" / "hdqspp_v3_frozen_wikitext2.yaml"
    frozen_path.parent.mkdir(parents=True, exist_ok=True)
    design = {
        "method": "hdqspp_v3",
        "dataset_key": "wikitext2_paper",
        "selection_split": "dev",
        "test_split_used_for_selection": False,
        "why_v2_failed": [
            "v2 full improved token/length JS diagnostics but worsened validation PPL.",
            "Stage 2.5 model-training ablations showed token-frequency preservation, "
            "strict distribution preservation, and length prior were likely harmful "
            "under this WikiText-2 small-model setup.",
            "WikiText-2 is curated, so aggressive filtering can remove useful coverage.",
        ],
        "removed_or_weakened_components": [
            "token_frequency_preservation removed",
            "length prior replaced by a weak length guardrail",
            "strict distribution-preserving selection replaced by soft calibrated selection",
        ],
        "retained_components": [
            "base document quality score",
            "quality/diversity balance",
            "capped repetition penalty",
        ],
        "new_mechanisms": [
            "keep-rate calibration at 0.85 to avoid v1-style hard filtering damage",
            "deterministic top-quality core plus soft weighted fill",
            "weak bin retention guardrails to reduce extreme length shift",
            "score-interleaved curriculum ordering for retained documents",
        ],
        "expected_advantage": (
            "Reduce v2 component-induced harm while preserving enough raw WikiText-2 "
            "coverage to compete with random and dedup baselines."
        ),
        "failure_risk": (
            "If raw WikiText-2 is already clean enough, any quality filtering may still "
            "underperform raw despite better diagnostics."
        ),
        "fair_comparison_protocol": [
            "same WikiText-2 official split",
            "same small model config",
            "same shared tokenizer/vocab/parameter_count",
            "same train token budget",
            "same evaluated validation token budget",
            "same seeds 1 2 3",
        ],
        "selected_config": asdict(base),
        "source_dev_evidence": [
            "artifacts/ablations/model_training_ablation_results.csv",
            "artifacts/methods/promising_variants.csv",
            "artifacts/diagnostics/hdqspp_failure_analysis.csv",
            "artifacts/stats/method_comparison_summary.csv",
        ],
        "source_run_ids": source_run_ids,
        "config_hash": config_hash(config_path),
    }
    design_path = methods_dir / "hdqspp_v3_design.json"
    report_path = methods_dir / "hdqspp_v3_freezing_report.md"
    design_path.write_text(json.dumps(design, indent=2, sort_keys=True), encoding="utf-8")
    frozen_payload = {
        "method": "hdqspp_v3",
        "dataset_key": "wikitext2_paper",
        "selection_split": "dev",
        "test_split_used_for_selection": False,
        "config": asdict(base),
        "source_design_artifact": "artifacts/methods/hdqspp_v3_design.json",
        "source_run_ids": source_run_ids,
    }
    frozen_path.write_text(json.dumps(frozen_payload, indent=2, sort_keys=True), encoding="utf-8")
    report_path.write_text(
        "# HDQS++ v3 Freezing Report\n\n"
        "- Method: `hdqspp_v3`\n"
        "- Selection split: `dev`\n"
        "- Test split used for selection: `false`\n"
        "- Frozen config: `configs/frozen/hdqspp_v3_frozen_wikitext2.yaml`\n"
        "- Evidence used: Stage 2.5 diagnostics, promising-variant selection, and "
        "model-training ablation rows.\n"
        "- Boundary: this freezes a candidate method; it does not claim supported "
        "improvement over raw.\n"
        f"- Source run IDs: `{'; '.join(source_run_ids)}`\n",
        encoding="utf-8",
    )
    record = append_run(
        {
            "run_id": make_run_id("freeze", "wikitext2_paper", "hdqspp_v3", now_utc()),
            "timestamp_utc": now_utc(),
            "command": f"python scripts/freeze_hdqspp_v3.py --config {args.config}",
            "config_path": args.config,
            "config_hash": config_hash(args.config),
            "dataset_key": "wikitext2_paper",
            "dataset_status": "real_local_nonfallback",
            "dataset_scope": "official_split",
            "model_size": "none",
            "model_config_path": "",
            "model_config_hash": "",
            "baseline_name": "freeze_hdqspp_v3",
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
            "metrics_path": relative(frozen_path),
            "model_quality_metric": "frozen_method_protocol_not_training_result",
        }
    )
    print(f"HDQS++ v3 frozen config: {frozen_path}")
    print(f"Design artifact: {design_path}")
    print(f"Registry row: {record['run_id']}")


if __name__ == "__main__":
    main()
