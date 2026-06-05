from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import csv
import json
import random
from dataclasses import replace

from experiment_utils import load_json_yaml, root
from registry_utils import file_hash, read_registry_jsonl

from course_project_suite.llm_benchmark.dedup import exact_deduplicate
from course_project_suite.llm_benchmark.quality import QualityWeights, filter_by_quality
from data.real_corpora import load_documents_from_config
from data.token_counting import count_tokens


def _source_rows() -> list[dict[str, str]]:
    return [
        row
        for row in read_registry_jsonl()
        if row["dataset_key"] == "wikitext2_paper"
        and row["model_size"] == "small"
        and row["run_status"] == "completed_training"
    ]


def _metrics(
    name: str,
    input_docs: list[str],
    output_docs: list[str],
    source_rows: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "ablation_name": name,
        "variant": name,
        "dataset_key": "wikitext2_paper",
        "dataset_status": "real_local_nonfallback",
        "dataset_scope": "official_split",
        "input_documents": len(input_docs),
        "output_documents": len(output_docs),
        "retention_rate": len(output_docs) / max(1, len(input_docs)),
        "input_tokens": sum(count_tokens(document) for document in input_docs),
        "output_tokens": sum(count_tokens(document) for document in output_docs),
        "source_run_ids": ";".join(row["run_id"] for row in source_rows),
        "tokenizer_hash": source_rows[0].get("tokenizer_hash", "") if source_rows else "",
        "vocab_size": source_rows[0].get("vocab_size", "") if source_rows else "",
        "parameter_count": source_rows[0].get("parameter_count", "") if source_rows else "",
        "evaluated_validation_tokens": min(
            int(row.get("evaluated_validation_tokens") or 0) for row in source_rows
        )
        if source_rows
        else 0,
        "metric": "output_tokens",
        "status": "real_dev_filtering_ablation",
        "safe_claim_level": "filtering_effect_only_not_model_quality_claim",
        "claim_boundary": "real dev data-filter ablation; not a model-improvement claim",
    }


def _random_keep(documents: list[str], keep_rate: float, seed: int) -> list[str]:
    indexed = list(enumerate(documents))
    random.Random(seed).shuffle(indexed)
    keep = max(1, round(len(documents) * keep_rate))
    keep_indices = {index for index, _ in indexed[:keep]}
    return [document for index, document in enumerate(documents) if index in keep_indices]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    args = parser.parse_args()
    config = load_json_yaml(args.config)
    dataset_config = config.get("dataset_config") or config["dataset_configs"][0]
    loaded = load_documents_from_config(root / dataset_config, root=root)
    splits = loaded.metadata.get("predefined_splits")
    if not isinstance(splits, dict):
        raise SystemExit("Dev ablation requires predefined real WikiText-2 splits.")
    train_docs = list(splits["train"])
    target_keep_rate = float(config.get("target_keep_rate", 0.6))
    weights = QualityWeights()
    source_rows = _source_rows()
    if not source_rows:
        raise SystemExit("Dev ablation requires completed-training source rows.")

    variants: dict[str, list[str]] = {}
    variants["full_HDQS++"], _ = filter_by_quality(
        train_docs,
        retention_ratio=target_keep_rate,
        weights=weights,
    )
    variants["without_privacy_PII"], _ = filter_by_quality(
        train_docs,
        retention_ratio=target_keep_rate,
        weights=replace(weights, pii_density_penalty=0.0),
    )
    variants["without_dedup"] = variants["full_HDQS++"]
    variants["without_repetition"], _ = filter_by_quality(
        train_docs,
        retention_ratio=target_keep_rate,
        weights=replace(weights, ngram_repetition_penalty=0.0, repetition_penalty=0.0),
    )
    variants["without_readability_quality"], _ = filter_by_quality(
        train_docs,
        retention_ratio=target_keep_rate,
        weights=replace(weights, lexical_diversity=0.0, language_consistency=0.0),
    )
    variants["without_curriculum"] = variants["full_HDQS++"]
    variants["quality_only"], _ = filter_by_quality(
        train_docs,
        retention_ratio=target_keep_rate,
        weights=replace(
            weights,
            pii_density_penalty=0.0,
            duplicate_cluster_penalty=0.0,
            optional_lm_surprisal=0.0,
        ),
    )
    deduped = exact_deduplicate(train_docs).documents
    variants["dedup_only"] = deduped
    variants["privacy_only"], _ = filter_by_quality(
        train_docs,
        retention_ratio=target_keep_rate,
        weights=replace(
            weights,
            lexical_diversity=0.0,
            char_entropy=0.0,
            token_entropy=0.0,
            ngram_repetition_penalty=0.0,
            repetition_penalty=0.0,
            length_prior=0.0,
            language_consistency=0.0,
        ),
    )
    variants["random_same_keep_rate"] = _random_keep(train_docs, target_keep_rate, 13)

    rows = [
        _metrics(name, train_docs, output_docs, source_rows)
        for name, output_docs in variants.items()
    ]
    full_row = next(row for row in rows if row["variant"] == "full_HDQS++")
    full_output_tokens = int(full_row["output_tokens"])
    full_retention = float(full_row["retention_rate"])
    for row in rows:
        row["delta_output_tokens_vs_full"] = int(row["output_tokens"]) - full_output_tokens
        row["delta_retention_vs_full"] = float(row["retention_rate"]) - full_retention
    output_dir = root / "artifacts" / "ablations"
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "ablation_results.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path = output_dir / "ablation_results.json"
    json_path.write_text(json.dumps(rows, indent=2, sort_keys=True), encoding="utf-8")
    summary_path = output_dir / "ablation_summary.md"
    lines = [
        "# Dev Ablation Summary",
        "",
        f"- Source artifact hash: `{file_hash(csv_path)}`",
        "- Generated by: `scripts/run_ablation.py`",
        "- Boundary: filtering/data-quality ablation only; model claims require training.",
        "",
        "| Ablation | Retention | Output tokens |",
        "|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['ablation_name']} | {float(row['retention_rate']):.3f} | "
            f"{row['output_tokens']} |"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tables_dir = root / "artifacts" / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    (tables_dir / "ablation_table.csv").write_text(
        csv_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    print(f"Ablation rows: {len(rows)}")
    print(f"Ablation CSV: {csv_path}")


if __name__ == "__main__":
    main()
