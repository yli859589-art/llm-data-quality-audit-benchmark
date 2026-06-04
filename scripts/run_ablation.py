from __future__ import annotations

import argparse
import csv
import json
from dataclasses import replace

from experiment_utils import load_json_yaml, root

from course_project_suite.llm_benchmark.dedup import exact_deduplicate
from course_project_suite.llm_benchmark.quality import QualityWeights, filter_by_quality
from data.real_corpora import load_documents_from_config
from data.token_counting import count_tokens


def _metrics(name: str, input_docs: list[str], output_docs: list[str]) -> dict[str, object]:
    return {
        "variant": name,
        "input_documents": len(input_docs),
        "output_documents": len(output_docs),
        "retention_rate": len(output_docs) / max(1, len(input_docs)),
        "input_tokens": sum(count_tokens(document) for document in input_docs),
        "output_tokens": sum(count_tokens(document) for document in output_docs),
        "claim_boundary": "data-filter ablation only; no model-quality claim",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/smoke.yaml")
    args = parser.parse_args()
    config = load_json_yaml(args.config)
    dataset_config = config.get("dataset_config") or config["dataset_configs"][0]
    loaded = load_documents_from_config(root / dataset_config, root=root)
    target_keep_rate = float(config.get("target_keep_rate", 0.6))
    weights = QualityWeights()
    variants = {
        "full_hdqspp": weights,
        "no_pii_penalty": replace(weights, pii_density_penalty=0.0),
        "no_ngram_repetition": replace(weights, ngram_repetition_penalty=0.0),
        "no_length_prior": replace(weights, length_prior=0.0),
    }
    rows = []
    for name, variant_weights in variants.items():
        retained, _ = filter_by_quality(
            loaded.documents,
            retention_ratio=target_keep_rate,
            weights=variant_weights,
        )
        rows.append(_metrics(name, loaded.documents, retained))
    deduped = exact_deduplicate(loaded.documents).documents
    retained_after_dedup, _ = filter_by_quality(
        deduped,
        retention_ratio=min(1.0, target_keep_rate),
        weights=weights,
    )
    rows.append(_metrics("dedup_then_hdqspp", loaded.documents, retained_after_dedup))

    output_dir = root / "artifacts" / "ablations" / str(config["experiment_key"])
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "ablation_results.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    (output_dir / "ablation_results.json").write_text(
        json.dumps(rows, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    lines = [
        "# HDQS++ Ablation Results",
        "",
        "| Variant | Output docs | Retention | Boundary |",
        "|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['variant']} | {row['output_documents']} | "
            f"{float(row['retention_rate']):.3f} | {row['claim_boundary']} |"
        )
    (output_dir / "ablation_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Ablation rows: {len(rows)}")
    print(f"Ablation CSV: {csv_path}")


if __name__ == "__main__":
    main()
