from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.data.manifests import build_dataset_manifest
from dataaudit_lm.data.records import make_record
from dataaudit_lm.data.sampling import corpus_wide_token_sample
from dataaudit_lm.data.splitting import cluster_aware_hash_split
from dataaudit_lm.filters.exact_dedup import apply_exact_dedup
from dataaudit_lm.filters.length import apply_length_filter
from dataaudit_lm.filters.minhash_dedup import apply_minhash_near_dedup
from dataaudit_lm.filters.quality_rules import apply_c4_quality_filter
from dataaudit_lm.filters.random_matched import apply_random_token_matched
from dataaudit_lm.filters.raw import apply_raw_filter
from dataaudit_lm.filters.reference_lm import FrozenUnigramReferenceLM, apply_reference_lm_filter
from dataaudit_lm.filters.selector import apply_dataaudit_selector
from dataaudit_lm.integrity.io import write_json, write_text
from dataaudit_lm.integrity.paths import REPORTS
from dataaudit_lm.models.config import DecoderLMConfig
from dataaudit_lm.training.initialization import manifest_to_dict, save_initialization_artifact
from dataaudit_lm.training.lineage import build_lineage
from dataaudit_lm.training.runner import TrainingConfig, run_tiny_training

OUT = ROOT / "artifacts" / "dataaudit_lm" / "rehearsal"


def _toy_records():
    rows = []
    base = [
        ("a", "alpha beta gamma useful text"),
        ("b", "alpha beta gamma useful text"),
        ("c", "alpha beta gamma useful rewrite"),
        ("d", "visit https://example.com <p>noise</p> 12345"),
        ("e", "finance markets coffee river stable words"),
        ("f", "scientific article with careful explanation"),
    ]
    for index in range(24):
        row_id, text = base[index % len(base)]
        rows.append(
            make_record(
                record_id=f"{row_id}_{index:03d}",
                source_row_id=str(index),
                text=f"{text} sample {index}",
                source_dataset="dataaudit_rehearsal_toy",
                source_revision="local_static_v1",
            )
        )
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    records = _toy_records()
    splits, split_manifest = cluster_aware_hash_split(records, seed=13)
    train_records = splits["train"] or records
    data_manifest = build_dataset_manifest(
        dataset_repository="dataaudit_rehearsal_toy",
        config="local_static",
        revision="v1",
        records=records,
        split_manifest=split_manifest,
        streaming_parameters={"source": "local_static_fixture"},
    )
    write_json(OUT / "data_manifest.json", data_manifest)

    reference = FrozenUnigramReferenceLM([record.text for record in train_records])
    filters = [
        apply_raw_filter(train_records),
        apply_exact_dedup(train_records),
        apply_minhash_near_dedup(train_records, threshold=0.5, ngram_size=2),
        apply_length_filter(train_records, min_tokens=3, max_tokens=12),
        apply_c4_quality_filter(train_records, min_score=0.25),
        apply_reference_lm_filter(train_records, reference_lm=reference, keep_lowest_fraction=0.5),
        apply_dataaudit_selector(train_records, reference_lm=reference, keep_fraction=0.5),
    ]
    length_target = next(
        item for item in filters if item.method_name == "length_filter"
    ).kept_tokens
    filters.append(
        apply_random_token_matched(
            train_records,
            target_tokens=max(1, length_target),
            seed=13,
            target_name="length",
        )
    )

    model_config = DecoderLMConfig(
        vocab_size=128, context_length=16, embedding_dim=16, hidden_dim=16
    )
    training_config = TrainingConfig(seed=13, steps=2, token_budget=256, batch_size=2)
    init_manifest = save_initialization_artifact(
        seed=13,
        config=model_config,
        output_dir=OUT / "initialization",
    )
    method_runs = []
    for filter_result in filters:
        method_dir = OUT / filter_result.method_name
        write_json(method_dir / "filter_manifest.json", filter_result.manifest)
        sample, sample_manifest = corpus_wide_token_sample(
            filter_result.kept_records,
            token_budget=training_config.token_budget,
            seed=13,
        )
        write_json(method_dir / "training_sample_manifest.json", asdict(sample_manifest))
        metrics = run_tiny_training(
            records=sample,
            model_config=model_config,
            training_config=training_config,
            output_dir=method_dir / "training",
        )
        lineage = build_lineage(
            data_manifest_hash=str(data_manifest["manifest_hash"]),
            filter_manifest_hash=str(filter_result.manifest["manifest_hash"]),
            sample_manifest_hash=sample_manifest.sample_manifest_hash,
            initialization_fingerprint=init_manifest.initialization_fingerprint,
            training_config=asdict(training_config),
        )
        write_json(method_dir / "lineage.json", lineage)
        method_runs.append(
            {
                "method_name": filter_result.method_name,
                "kept_count": len(filter_result.kept_records),
                "kept_tokens": filter_result.kept_tokens,
                "sampled_tokens": sample_manifest.sampled_token_count,
                "initialization_fingerprint": init_manifest.initialization_fingerprint,
                "warm_start": False,
                "metrics": metrics,
                "status": "completed",
            }
        )

    report = {
        "status": "passed",
        "scope": "ENGINEERING_VALIDATION_ONLY",
        "comparison_scope": "NOT_FOR_METHOD_COMPARISON",
        "dataset_count": 1,
        "seed_count": 1,
        "token_budget": training_config.token_budget,
        "initialization_manifest": manifest_to_dict(init_manifest),
        "runs": method_runs,
        "all_nll_finite": all(
            run["metrics"]["valid_nll_nats_per_token"] < float("inf") for run in method_runs
        ),
        "all_warm_start_false": all(run["warm_start"] is False for run in method_runs),
    }
    write_json(REPORTS / "rehearsal_report.json", report)
    lines = [
        "# DataAudit-LM Rehearsal Report",
        "",
        "- Status: `passed`",
        "- Scope: `ENGINEERING_VALIDATION_ONLY`",
        "- Comparison scope: `NOT_FOR_METHOD_COMPARISON`",
        f"- Methods: `{len(method_runs)}`",
        f"- Seed count: `{report['seed_count']}`",
        f"- Token budget: `{report['token_budget']}`",
    ]
    write_text(REPORTS / "rehearsal_report.md", "\n".join(lines))
    print(json.dumps({"rehearsal_passed": True, "methods": len(method_runs)}))


if __name__ == "__main__":
    main()
