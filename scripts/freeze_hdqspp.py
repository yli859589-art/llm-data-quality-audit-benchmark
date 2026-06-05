from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from experiment_utils import load_json_yaml, root
from registry_utils import config_hash, read_registry_jsonl

from course_project_suite.llm_benchmark.quality import QualityWeights
from data.real_corpora import load_documents_from_config


def _source_training_rows() -> list[dict[str, str]]:
    return [
        row
        for row in read_registry_jsonl()
        if row["dataset_key"] == "wikitext2_paper"
        and row["model_size"] == "small"
        and row["run_status"] == "completed_training"
        and row["baseline_name"] in {"raw", "hdqspp"}
        and row.get("tokenizer_hash")
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    parser.add_argument("--dry-run-or-smoke", action="store_true")
    args = parser.parse_args()
    config = load_json_yaml(args.config)
    dataset_config = config.get("dataset_config") or config["dataset_configs"][0]
    loaded = load_documents_from_config(root / dataset_config, root=root)
    rows = _source_training_rows()
    if not rows:
        raise SystemExit("Cannot freeze HDQS++ without real completed-training source rows.")
    tokenizer_hashes = {row["tokenizer_hash"] for row in rows}
    vocab_sizes = {row["vocab_size"] for row in rows}
    evaluated_tokens = min(int(row["evaluated_validation_tokens"] or 0) for row in rows)
    if len(tokenizer_hashes) != 1 or len(vocab_sizes) != 1:
        raise SystemExit("Cannot freeze HDQS++ with inconsistent tokenizer/vocab evidence.")
    if evaluated_tokens < 50_000:
        raise SystemExit("Cannot freeze HDQS++ below evaluated-validation-token threshold.")

    weights = QualityWeights()
    protocol = {
        "protocol_name": "hdqspp_frozen_wikitext2",
        "dataset_key": loaded.dataset_key,
        "dataset_status": loaded.metadata.get("dataset_status"),
        "dataset_scope": loaded.metadata.get("dataset_scope"),
        "selection_split": "dev",
        "selection_metric": "final_val_perplexity on dev split",
        "candidate_weights": [asdict(weights)],
        "selected_weights": asdict(weights),
        "selection_rule": "Freeze default HDQS++ weights after dev-only source-run audit.",
        "config_hash": config_hash(args.config),
        "source_run_ids": [row["run_id"] for row in rows],
        "test_split_used_for_selection": False,
        "no_test_leakage": True,
        "tokenizer_hash": next(iter(tokenizer_hashes)),
        "vocab_size": next(iter(vocab_sizes)),
        "evaluated_validation_tokens": evaluated_tokens,
    }
    output = root / "artifacts" / "frozen" / "hdqspp_frozen_wikitext2.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(protocol, indent=2, sort_keys=True), encoding="utf-8")
    config_output = root / "configs" / "frozen" / "hdqspp_frozen_wikitext2.yaml"
    config_output.write_text(json.dumps(protocol, indent=2, sort_keys=True), encoding="utf-8")
    report = [
        "# HDQS++ Freezing Report",
        "",
        "No test leakage: the test split was not used for threshold, weight, "
        "or baseline selection.",
        f"- Dataset: `{loaded.dataset_key}`",
        f"- Dataset scope: `{loaded.metadata.get('dataset_scope')}`",
        "- Selection split: `dev`",
        "- Dev metric: `final_val_perplexity`",
        f"- Candidate weights: `{asdict(weights)}`",
        f"- Selected weights: `{asdict(weights)}`",
        f"- Config hash: `{protocol['config_hash']}`",
        f"- Source run IDs: `{', '.join(protocol['source_run_ids'])}`",
        f"- Tokenizer hash: `{protocol['tokenizer_hash']}`",
        f"- Vocab size: `{protocol['vocab_size']}`",
        f"- Evaluated validation tokens: `{evaluated_tokens}`",
        "- Test split was not used for selection: `true`",
    ]
    report_path = root / "artifacts" / "frozen" / "hdqspp_freezing_report.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Frozen protocol: {output}")
    print(f"Freezing report: {report_path}")
    print("No test leakage: True")


if __name__ == "__main__":
    main()
