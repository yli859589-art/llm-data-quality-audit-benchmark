from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import csv
import json
from typing import Any

from experiment_utils import root
from registry_utils import read_registry_jsonl

REQUIRED_BASELINES = [
    "raw",
    "random_same_keep_rate",
    "length_filter",
    "dedup_only",
    "hdqspp",
    "hdqspp_v2",
    "hdqspp_v2_no_token_frequency",
    "hdqspp_v3",
]
REQUIRED_SEEDS = ["1", "2", "3"]
MIN_TRAIN_TOKENS = 1_000_000
MIN_EVALUATED_VALIDATION_TOKENS = 50_000
REQUIRED_ABLATIONS = {
    "full_HDQS++",
    "without_privacy_PII",
    "without_dedup",
    "without_repetition",
    "without_readability_quality",
    "without_curriculum",
    "quality_only",
    "dedup_only",
    "privacy_only",
    "random_same_keep_rate",
}
MULTI_DATASET_METHODS = {"raw", "random_same_keep_rate", "dedup_only", "hdqspp_v3"}
MULTI_DATASET_SEEDS = {"1", "2", "3"}
STREAMING_DATASETS = {"openwebtext_streaming", "c4_en_streaming"}


def _exists(path: str) -> bool:
    return (root / path).exists()


def _load_json(path: str) -> dict[str, Any]:
    file_path = root / path
    if not file_path.exists():
        return {}
    return json.loads(file_path.read_text(encoding="utf-8"))


def _read_csv(path: str) -> list[dict[str, str]]:
    file_path = root / path
    if not file_path.exists():
        return []
    with file_path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _count_registry_rows() -> int:
    path = root / "artifacts" / "runs" / "run_registry.csv"
    if not path.exists():
        return 0
    return max(0, len(path.read_text(encoding="utf-8").splitlines()) - 1)


def _paper_manifest() -> dict[str, Any]:
    return _load_json("artifacts/data/wikitext2_paper/data_manifest.json")


def _has_real_nonfallback_manifest() -> bool:
    manifest = _paper_manifest()
    return (
        bool(manifest)
        and bool(manifest.get("required_real_data"))
        and not manifest.get("used_fallback")
        and manifest.get("dataset_status") in {"real_nonfallback", "real_local_nonfallback"}
        and manifest.get("dataset_scope") == "official_split"
    )


def _manifest_has_split_hashes() -> bool:
    manifest = _paper_manifest()
    split_hashes = manifest.get("split_document_hashes", {})
    if not isinstance(split_hashes, dict):
        return False
    return all(split_hashes.get(split) for split in ["train", "dev", "test"])


def _report_passed(path: str) -> bool:
    payload = _load_json(path)
    return payload.get("status") == "passed"


def _candidate_training_rows() -> list[dict[str, Any]]:
    rows = []
    for row in read_registry_jsonl():
        if row.get("dataset_key") != "wikitext2_paper":
            continue
        if row.get("dataset_status") not in {"real_nonfallback", "real_local_nonfallback"}:
            continue
        if row.get("dataset_scope") != "official_split":
            continue
        if row.get("model_size") != "small":
            continue
        if row.get("run_status") != "completed_training":
            continue
        if row.get("baseline_name") not in REQUIRED_BASELINES:
            continue
        if str(row.get("seed")) not in REQUIRED_SEEDS:
            continue
        rows.append(row)
    return rows


def _int(row: dict[str, Any], field: str) -> int:
    try:
        return int(float(row.get(field, 0) or 0))
    except (TypeError, ValueError):
        return 0


def _completed_training_matrix() -> bool:
    rows = _candidate_training_rows()
    seen = {(str(row.get("baseline_name")), str(row.get("seed"))) for row in rows}
    expected = {(baseline, seed) for baseline in REQUIRED_BASELINES for seed in REQUIRED_SEEDS}
    if not expected.issubset(seen):
        return False
    for row in rows:
        if _int(row, "train_tokens") < MIN_TRAIN_TOKENS:
            return False
        if _int(row, "evaluated_validation_tokens") < MIN_EVALUATED_VALIDATION_TOKENS:
            return False
        if (
            not row.get("tokenizer_hash")
            or not row.get("vocab_size")
            or not row.get("parameter_count")
        ):
            return False
    return True


def _fair_tokenizer_budget() -> bool:
    rows = _candidate_training_rows()
    fields = ["tokenizer_hash", "vocab_size", "parameter_count"]
    for field in fields:
        values = {str(row.get(field, "")) for row in rows if row.get(field) not in {"", None}}
        if len(values) != 1:
            return False
    for field in [
        "train_tokens",
        "evaluated_validation_tokens",
        "eval_batch_size",
        "eval_block_size",
    ]:
        values = {str(row.get(field, "")) for row in rows if row.get(field) not in {"", None}}
        if len(values) != 1:
            return False
    return bool(rows)


def _frozen_real_dev() -> bool:
    frozen = _load_json("artifacts/frozen/hdqspp_frozen_wikitext2.json")
    if not frozen:
        return False
    return (
        frozen.get("dataset_key") == "wikitext2_paper"
        and frozen.get("selection_split") == "dev"
        and frozen.get("test_split_used_for_selection") is False
        and bool(frozen.get("source_run_ids"))
        and bool(frozen.get("tokenizer_hash"))
        and _int(frozen, "evaluated_validation_tokens") >= MIN_EVALUATED_VALIDATION_TOKENS
    )


def _ablation_complete() -> bool:
    rows = _read_csv("artifacts/ablations/ablation_results.csv")
    variants = {row.get("variant", "") for row in rows}
    if not REQUIRED_ABLATIONS.issubset(variants):
        return False
    return all(row.get("dataset_key") == "wikitext2_paper" for row in rows)


def _significance_complete() -> bool:
    rows = _read_csv("artifacts/stats/significance_tests.csv")
    comparisons = {row.get("comparison", "") for row in rows}
    expected = {f"{baseline}_vs_raw" for baseline in REQUIRED_BASELINES if baseline != "raw"}
    if not expected.issubset(comparisons):
        return False
    safe_claims = {row.get("safe_claim_level", "") for row in rows}
    return all("statistically_supported" not in claim for claim in safe_claims)


def _main_results_pure() -> bool:
    rows = _read_csv("artifacts/tables/main_results.csv")
    if not rows:
        return False
    required_pairs = {
        (baseline, seed) for baseline in REQUIRED_BASELINES for seed in REQUIRED_SEEDS
    }
    present = {(row.get("baseline_name", ""), row.get("seed", "")) for row in rows}
    if not required_pairs.issubset(present):
        return False
    return all(
        row.get("run_status") == "completed_training"
        and row.get("dataset_status") in {"real_nonfallback", "real_local_nonfallback"}
        and int(row.get("evaluated_validation_tokens", "0") or 0) >= MIN_EVALUATED_VALIDATION_TOKENS
        and row.get("tokenizer_hash")
        for row in rows
    )


def _claim_map_traceable() -> bool:
    rows = _read_csv("docs/CLAIM_ARTIFACT_MAP.csv")
    if not rows:
        return False
    required_columns = {
        "Claim",
        "Artifact Path",
        "Script",
        "Source Run IDs",
        "Dataset",
        "Dataset Status",
        "Dataset Scope",
        "Baseline",
        "Model Size",
        "Seeds",
        "Tokenizer Hash",
        "Vocab Size",
        "Parameter Count",
        "Train Tokens",
        "Evaluated Validation Tokens",
        "Metric",
        "CI",
        "Status",
        "Safe Claim Level",
    }
    return required_columns.issubset(rows[0])


def _tables_figures_complete() -> bool:
    required = [
        "artifacts/tables/main_results.csv",
        "artifacts/tables/filtering_results.csv",
        "artifacts/tables/smoke_results.csv",
        "artifacts/tables/lightweight_dev_results.csv",
        "artifacts/tables/model_training_results.csv",
        "artifacts/tables/ablation_table.csv",
        "artifacts/figures/seed_confidence_intervals.svg",
        "artifacts/figures/privacy_utility_tradeoff.svg",
        "artifacts/figures/ablation_effects.svg",
        "artifacts/figures/model_scale_comparison.svg",
    ]
    return all(_exists(path) for path in required)


def _method_artifacts_complete() -> bool:
    required = [
        "artifacts/diagnostics/hdqspp_failure_analysis.csv",
        "artifacts/diagnostics/hdqspp_failure_analysis.json",
        "artifacts/diagnostics/hdqspp_failure_analysis.md",
        "artifacts/method_debug/method_debug_results.csv",
        "artifacts/methods/hdqspp_v2_design.json",
        "artifacts/methods/hdqspp_v2_component_weights.json",
        "artifacts/methods/hdqspp_v2_freezing_report.md",
        "artifacts/methods/promising_variants.csv",
        "artifacts/methods/promising_variants.json",
        "artifacts/methods/promising_variants.md",
        "artifacts/methods/hdqspp_v3_design.json",
        "artifacts/methods/hdqspp_v3_freezing_report.md",
        "configs/frozen/hdqspp_v2_frozen_wikitext2.yaml",
        "configs/frozen/hdqspp_v3_frozen_wikitext2.yaml",
        "artifacts/ablations/model_training_ablation_results.csv",
        "artifacts/ablations/v3_model_ablation_results.csv",
        "artifacts/ablations/v3_model_ablation_results.json",
        "artifacts/ablations/v3_model_ablation_summary.md",
        "artifacts/diagnostics/method_error_cases.csv",
        "artifacts/figures/method_component_correlation.svg",
        "artifacts/figures/distribution_shift_after_filtering.svg",
        "artifacts/figures/keep_rate_vs_validation_ppl.svg",
        "artifacts/figures/v3_ablation_effects.svg",
        "artifacts/figures/method_comparison_ci.svg",
        "artifacts/figures/v3_vs_baselines.svg",
        "artifacts/figures/keep_rate_vs_ppl.svg",
        "artifacts/figures/component_effects_v3.svg",
        "artifacts/figures/promising_variant_selection.svg",
        "docs/METHOD_DASHBOARD.md",
        "docs/PROJECT_EVIDENCE_MAP.md",
    ]
    return all(_exists(path) for path in required)


def _method_status() -> str:
    repositioning = root / "docs" / "PROJECT_REPOSITIONING.md"
    if repositioning.exists():
        text = repositioning.read_text(encoding="utf-8", errors="ignore")
        if "honest_audit_framework" in text:
            return "honest_audit_framework"
    status_report = root / "artifacts" / "stats" / "method_status_report.md"
    if status_report.exists():
        text = status_report.read_text(encoding="utf-8", errors="ignore")
        for status in [
            "method_supported_over_raw",
            "method_trend_improved_over_raw",
            "method_improves_over_prior_hdqs_but_not_raw",
            "method_unsupported",
            "baseline_underperforms_raw",
        ]:
            if f"`{status}`" in text:
                return status
        if "`method_unsupported_over_raw`" in text:
            return "method_unsupported"
    rows = _read_csv("artifacts/stats/method_comparison_summary.csv")
    if not rows:
        return "method_unsupported"
    by_name = {row.get("comparison", ""): row for row in rows}
    primary = "hdqspp_v3_vs_raw" if "hdqspp_v3_vs_raw" in by_name else "hdqspp_v2_vs_raw"
    raw = by_name.get(primary)
    v1 = by_name.get("hdqspp_v3_vs_hdqspp") or by_name.get("hdqspp_v2_vs_hdqspp")
    if not raw:
        return "method_unsupported"

    def diff(row: dict[str, str] | None) -> float:
        if not row:
            return 0.0
        try:
            return float(
                row.get("mean_difference_reference_minus_candidate")
                or row.get("mean_difference_reference_minus_v2", "0")
                or 0
            )
        except ValueError:
            return 0.0

    raw_diff = diff(raw)
    v1_diff = diff(v1)
    raw_status = raw.get("status", "")
    raw_n = int(float(raw.get("n_paired_seeds", "0") or 0))
    raw_low = float(raw.get("ci95_low", "0") or 0)
    if raw_n >= 5 and raw_low > 0 and raw_status == "supported_over_reference":
        return "method_supported_over_raw"
    if raw_diff > 0:
        return "method_trend_improved_over_raw"
    if v1_diff > 0:
        return "method_improves_over_prior_hdqs_but_not_raw"
    if raw_diff < 0:
        return "baseline_underperforms_raw"
    return "method_unsupported"


def _benchmark_scope_status() -> str:
    rows = read_registry_jsonl()

    def dataset_complete(dataset: str) -> bool:
        seen = {
            (row.get("baseline_name", ""), str(row.get("seed", "")))
            for row in rows
            if row.get("dataset_key") == dataset
            and row.get("dataset_status") == "real_nonfallback"
            and row.get("dataset_scope") == "streaming_sample"
            and row.get("run_status") == "completed_training"
            and row.get("baseline_name") in MULTI_DATASET_METHODS
            and str(row.get("seed")) in MULTI_DATASET_SEEDS
            and row.get("tokenizer_hash")
            and row.get("vocab_size")
            and row.get("parameter_count")
        }
        expected = {
            (method, seed)
            for method in MULTI_DATASET_METHODS
            for seed in MULTI_DATASET_SEEDS
        }
        return expected.issubset(seen)

    completed_datasets = {dataset for dataset in STREAMING_DATASETS if dataset_complete(dataset)}
    if completed_datasets == STREAMING_DATASETS:
        return "multi_dataset_audit_candidate"
    if completed_datasets:
        return "multi_dataset_partial"

    status_rows = _read_csv("artifacts/cross_dataset/dataset_status_matrix.csv")
    by_dataset = {row.get("dataset", ""): row for row in status_rows}
    failure_like = {
        "failed_due_to_network",
        "failed_due_to_auth",
        "failed_due_to_disk",
        "failed_due_to_environment",
        "insufficient_streaming_sample",
        "dataset_debug",
    }
    if STREAMING_DATASETS.issubset(by_dataset) and all(
        by_dataset[dataset].get("dataset_status") in failure_like
        for dataset in STREAMING_DATASETS
    ):
        return "multi_dataset_failed_due_to_environment"
    return "single_dataset_candidate"


def main() -> None:
    checks = {
        "data_configs": all(
            _exists(path)
            for path in [
                "configs/data/wikitext2_smoke.yaml",
                "configs/data/wikitext2_paper.yaml",
                "configs/data/openwebtext_smoke.yaml",
                "configs/data/openwebtext_paper.yaml",
                "configs/data/c4_en_smoke.yaml",
                "configs/data/c4_en_paper.yaml",
            ]
        ),
        "experiment_configs": all(
            _exists(path)
            for path in [
                "configs/experiments/smoke.yaml",
                "configs/experiments/dev.yaml",
                "configs/experiments/paper_wikitext2.yaml",
                "configs/experiments/paper_openwebtext.yaml",
                "configs/experiments/paper_c4.yaml",
                "configs/experiments/full_all.yaml",
            ]
        ),
        "smoke_manifest": _exists("artifacts/data/wikitext2_smoke/data_manifest.json"),
        "baseline_registry_rows": _count_registry_rows(),
        "real_nonfallback_manifest": _has_real_nonfallback_manifest(),
        "manifest_split_hashes": _manifest_has_split_hashes(),
        "split_integrity": _report_passed(
            "artifacts/data/wikitext2_paper/split_integrity_report.json"
        ),
        "completed_training_6x3_matrix": _completed_training_matrix(),
        "fair_tokenizer_budget": _fair_tokenizer_budget(),
        "frozen_real_dev_protocol": _frozen_real_dev(),
        "no_test_leakage": _report_passed("artifacts/frozen/no_test_leakage_report.json"),
        "ablation_complete": _ablation_complete(),
        "significance_complete": _significance_complete(),
        "main_results_pure": _main_results_pure(),
        "tables_figures": _tables_figures_complete(),
        "claim_map_traceable": _claim_map_traceable(),
        "migration_log": _exists("artifacts/runs/migration_log.jsonl"),
        "method_artifacts_complete": _method_artifacts_complete(),
    }
    basic_missing = [
        name
        for name in ["data_configs", "experiment_configs", "smoke_manifest"]
        if not checks[name]
    ]
    candidate_missing = [
        name
        for name in [
            "real_nonfallback_manifest",
            "manifest_split_hashes",
            "split_integrity",
            "completed_training_6x3_matrix",
            "fair_tokenizer_budget",
            "frozen_real_dev_protocol",
            "no_test_leakage",
            "ablation_complete",
            "significance_complete",
            "main_results_pure",
            "tables_figures",
            "claim_map_traceable",
            "migration_log",
            "method_artifacts_complete",
        ]
        if not checks[name]
    ]
    partial = (
        checks["real_nonfallback_manifest"]
        and checks["baseline_registry_rows"]
        and checks["main_results_pure"]
    )
    if basic_missing:
        level = "FAIL"
        level_reason = "Required baseline project infrastructure is missing."
    elif not candidate_missing:
        level = "EXPERIMENT-CANDIDATE"
        level_reason = (
            "WikiText-2 real non-fallback dev evidence includes a fair-tokenizer "
            "small-model baseline and candidate matrix, HDQS++ v2/v3 diagnostics, "
            "frozen protocols, ablation, statistics, tables, figures, and traceable claim map."
        )
    elif partial:
        level = "EXPERIMENT-CANDIDATE-PARTIAL"
        level_reason = (
            "Some real WikiText-2 completed-training evidence exists, but candidate "
            f"requirements are still missing: {', '.join(candidate_missing)}."
        )
    else:
        level = "PROTOTYPE"
        level_reason = (
            "The infrastructure exists, but real non-fallback candidate evidence is incomplete."
        )

    benchmark_scope_status = _benchmark_scope_status()
    if benchmark_scope_status == "multi_dataset_audit_candidate":
        remaining_to_ccf_c_ready = [
            "Scale beyond bounded OpenWebText/C4 streaming samples before paper-scale claims.",
            "Run larger model scales and a stronger seed budget before statistical claims.",
            "Evaluate on held-out test splits only after freezing dev-selected settings.",
            "Attach compute logs, environment hashes, reviewer-facing error analysis, "
            "and policy disclosure.",
        ]
    else:
        remaining_to_ccf_c_ready = [
            "Add OpenWebText and C4 real non-fallback streaming-sample experiments under the same protocol.",
            "Run larger model scales and a stronger seed budget before statistical claims.",
            "Evaluate on held-out test splits only after freezing dev-selected settings.",
            "Attach compute logs, environment hashes, reviewer-facing error analysis, "
            "and policy disclosure.",
        ]

    report = {
        "readiness_level": level,
        "level_reason": level_reason,
        "checks": checks,
        "basic_missing": basic_missing,
        "candidate_missing": candidate_missing,
        "method_status": _method_status(),
        "benchmark_scope_status": benchmark_scope_status,
        "ccf_c_ready": False,
        "remaining_to_ccf_c_ready": remaining_to_ccf_c_ready,
    }
    output_json = root / "artifacts" / "experiment_readiness_report.json"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md = [
        "# Experiment Readiness Report",
        "",
        f"- Readiness level: `{level}`",
        f"- Reason: {level_reason}",
        f"- CCF-C experiment ready: `{report['ccf_c_ready']}`",
        f"- Method status: `{report['method_status']}`",
        f"- Benchmark scope status: `{report['benchmark_scope_status']}`",
        "",
        "## Checks",
        "",
    ]
    for name, value in checks.items():
        md.append(f"- `{name}`: `{value}`")
    md.extend(["", "## Candidate Missing", ""])
    if candidate_missing:
        md.extend(f"- `{item}`" for item in candidate_missing)
    else:
        md.append("- None for WikiText-2 dev candidate scope.")
    md.extend(["", "## Remaining Work To CCF-C Ready", ""])
    md.extend(f"- {item}" for item in report["remaining_to_ccf_c_ready"])
    (root / "docs" / "EXPERIMENT_READINESS_REPORT.md").write_text(
        "\n".join(md) + "\n",
        encoding="utf-8",
    )
    print(f"Experiment readiness: {level}")
    print(f"Report: {output_json}")
    if level == "FAIL":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
