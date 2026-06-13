from __future__ import annotations

import csv
import json
import shutil
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from localmax_utils import ROOT, protected_hashes, protected_hashes_unchanged, sha256_file, write_csv, write_json
from artifacts_v2.canonical_io import write_canonical_text


RELEASE_ROOT = ROOT / "artifacts" / "localmax_release"
TABLES_DIR = RELEASE_ROOT / "tables"
REPORTS_DIR = RELEASE_ROOT / "reports"
MANIFESTS_DIR = RELEASE_ROOT / "manifests"
SOURCE_TABLES = ROOT / "artifacts" / "localmax_tables"
EVALUATION_DIR = ROOT / "artifacts" / "localmax_evaluation_strengthened"
ANALYSIS_DIR = ROOT / "artifacts" / "localmax_analysis_strengthened"
CURRENT_READINESS = "LOCAL_MAX_MINIMAL_TRAINING_EVIDENCE_RELEASED"
FROZEN_RELEASE_TIMESTAMP = "2026-06-12T00:00:00Z"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _float(value: str) -> float:
    return float(value) if str(value).strip() else 0.0


def _int(value: str) -> int:
    return int(float(value)) if str(value).strip() else 0


def _mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def _stdev(values: list[float]) -> float:
    return statistics.pstdev(values) if len(values) > 1 else 0.0


def _release_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _copy_json(source: Path, target: Path) -> str:
    payload = _load_json(source)
    write_json(target, payload)
    return _release_path(target)


def _copy_text(source: Path, target: Path) -> str:
    write_canonical_text(target, source.read_text(encoding="utf-8"))
    return _release_path(target)


def _reset_metadata_dirs() -> None:
    if MANIFESTS_DIR.exists():
        shutil.rmtree(MANIFESTS_DIR)
    for name in ["data", "tokenizer", "filters", "training", "evaluation", "analysis", "reports"]:
        path = MANIFESTS_DIR / name
        path.mkdir(parents=True, exist_ok=True)


def _standalone_training_dir(row: dict[str, str]) -> Path:
    return MANIFESTS_DIR / "training" / row["dataset"] / row["method"] / f"seed_{row['seed']}"


def _copy_standalone_metadata(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    _reset_metadata_dirs()
    data_report = _load_json(ROOT / "artifacts" / "reports" / "localmax_data_report.json")
    for item in data_report.get("datasets", []):
        dataset = item.get("dataset_id", "unknown_dataset")
        for key in ["manifest_path", "data_manifest_path"]:
            rel_path = item.get(key)
            if rel_path and (ROOT / rel_path).exists():
                _copy_json(ROOT / rel_path, MANIFESTS_DIR / "data" / dataset / Path(rel_path).name)

    tokenizer_manifest = ROOT / "artifacts" / "localmax_tokenizers" / "gpt2" / "tokenizer_manifest.json"
    if tokenizer_manifest.exists():
        _copy_json(tokenizer_manifest, MANIFESTS_DIR / "tokenizer" / "gpt2" / "tokenizer_manifest.json")

    for filter_manifest in sorted((ROOT / "artifacts" / "localmax_filters").glob("*/*/filter_manifest.json")):
        dataset = filter_manifest.parent.parent.name
        method = filter_manifest.parent.name
        _copy_json(filter_manifest, MANIFESTS_DIR / "filters" / dataset / method / "filter_manifest.json")

    release_rows: list[dict[str, str]] = []
    for row in source_rows:
        release_row = dict(row)
        source_manifest = ROOT / row["training_manifest"]
        manifest = _load_json(source_manifest)
        target_dir = _standalone_training_dir(row)
        release_row["training_manifest"] = _copy_json(source_manifest, target_dir / "training_manifest.json")
        for key in ["metrics_path", "checkpoint_manifest_path", "lineage_path", "runtime_cost_path"]:
            rel_path = manifest.get(key)
            if rel_path and (ROOT / rel_path).exists():
                _copy_json(ROOT / rel_path, target_dir / Path(rel_path).name)
        release_row["evaluation_manifest"] = "artifacts/localmax_release/manifests/evaluation/evaluation_manifest.json"
        release_rows.append(release_row)

    for source in sorted(EVALUATION_DIR.glob("*")):
        if source.is_file():
            target = MANIFESTS_DIR / "evaluation" / source.name
            if source.suffix == ".json":
                _copy_json(source, target)
            else:
                _copy_text(source, target)
    for source in sorted(ANALYSIS_DIR.glob("*")):
        if source.is_file():
            target = MANIFESTS_DIR / "analysis" / source.name
            if source.suffix == ".json":
                _copy_json(source, target)
            else:
                _copy_text(source, target)
    for source in sorted((ROOT / "artifacts" / "reports").glob("localmax_*_report.json")):
        _copy_json(source, MANIFESTS_DIR / "reports" / source.name)
    return release_rows


def _write_report(payload: dict[str, Any]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORTS_DIR / "localmax_tables_report.json", payload)
    lines = [
        "# LocalMax Release Tables Report",
        "",
        f"- Status: `{payload['status']}`",
        f"- Current readiness: `{payload['current_readiness']}`",
        f"- Main release rows: `{payload['main_release_rows']}`",
        f"- Table count: `{len(payload['table_hashes'])}`",
        f"- Historical results modified: `{payload['historical_results_modified']}`",
        "",
        "## Tables",
        "",
    ]
    for name, digest in payload["table_hashes"].items():
        lines.append(f"- `{name}`: `{digest}`")
    lines.extend(["", "## Blocking Failures", ""])
    lines.extend([f"- {item}" for item in payload["blocking_failures"]] or ["- none"])
    write_canonical_text(REPORTS_DIR / "localmax_tables_report.md", "\n".join(lines))


def build_release_tables() -> dict[str, Any]:
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    blocking: list[str] = []

    main_rows = _read_csv(SOURCE_TABLES / "localmax_main_results.csv")
    if len(main_rows) != 24:
        blocking.append(f"Expected 24 LocalMax main rows, found {len(main_rows)}.")
    for index, row in enumerate(main_rows, start=1):
        if row.get("metric_for_comparison") != "valid_loss":
            blocking.append(f"Row {index} metric_for_comparison is not valid_loss.")
        if not row.get("valid_loss"):
            blocking.append(f"Row {index} is missing valid_loss.")
        if row.get("ppl_clipped") not in {"True", "true", "1"}:
            blocking.append(f"Row {index} does not disclose ppl_clipped=true.")
        if row.get("ppl_comparable") not in {"False", "false", "0"}:
            blocking.append(f"Row {index} does not disclose ppl_comparable=false.")
        for field in ["training_manifest", "evaluation_manifest"]:
            value = row.get(field, "")
            if not value or not (ROOT / value).exists():
                blocking.append(f"Row {index} missing linked artifact for {field}: {value}")
    release_rows = _copy_standalone_metadata(main_rows)

    release_main = TABLES_DIR / "localmax_main_results_release.csv"
    main_fields = [
        "dataset",
        "method",
        "seed",
        "model_scale",
        "steps_completed",
        "tokens_seen",
        "valid_loss",
        "valid_ppl_clipped",
        "ppl_clipped",
        "ppl_comparable",
        "metric_for_comparison",
        "training_manifest",
        "evaluation_manifest",
        "evidence_level",
    ]
    write_csv(release_main, main_fields, release_rows)

    rdc_rows = _read_csv(EVALUATION_DIR / "risk_diversity_cost.csv")
    rdc_by_key = {(row["dataset_id"], row["method_name"]): row for row in rdc_rows}
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in release_rows:
        grouped[(row["dataset"], row["method"])].append(row)

    method_rows: list[dict[str, Any]] = []
    for dataset in sorted({key[0] for key in grouped}):
        dataset_groups = [(method, rows) for (group_dataset, method), rows in grouped.items() if group_dataset == dataset]
        ranked = sorted(dataset_groups, key=lambda item: _mean([_float(row["valid_loss"]) for row in item[1]]))
        rank_by_method = {method: rank for rank, (method, _) in enumerate(ranked, start=1)}
        raw_mean = next(
            (_mean([_float(row["valid_loss"]) for row in rows]) for method, rows in dataset_groups if method == "raw"),
            0.0,
        )
        for method, rows in sorted(dataset_groups):
            losses = [_float(row["valid_loss"]) for row in rows]
            risk_row = rdc_by_key.get((dataset, method), {})
            mean_loss = _mean(losses)
            method_rows.append(
                {
                    "dataset": dataset,
                    "method": method,
                    "n_seeds": len(rows),
                    "mean_valid_loss": mean_loss,
                    "std_valid_loss": _stdev(losses),
                    "rank_by_valid_loss": rank_by_method[method],
                    "raw_minus_method_valid_loss": raw_mean - mean_loss,
                    "risk": risk_row.get("risk", ""),
                    "diversity": risk_row.get("diversity", ""),
                    "cost": risk_row.get("cost", ""),
                    "metric_for_comparison": "valid_loss",
                    "ppl_comparable": "False",
                    "improvement_claim_allowed": "False",
                    "evidence_level": "localmax_minimal_training_evidence",
                }
            )

    write_csv(
        TABLES_DIR / "localmax_method_summary_release.csv",
        [
            "dataset",
            "method",
            "n_seeds",
            "mean_valid_loss",
            "std_valid_loss",
            "rank_by_valid_loss",
            "raw_minus_method_valid_loss",
            "risk",
            "diversity",
            "cost",
            "metric_for_comparison",
            "ppl_comparable",
            "improvement_claim_allowed",
            "evidence_level",
        ],
        method_rows,
    )

    data_report = _load_json(ROOT / "artifacts" / "reports" / "localmax_data_report.json")
    dataset_rows = []
    for item in data_report.get("datasets", []):
        source_data_manifest = item.get("data_manifest_path", item.get("manifest_path", ""))
        release_data_manifest = (
            f"artifacts/localmax_release/manifests/data/{item.get('dataset_id', 'unknown_dataset')}/{Path(source_data_manifest).name}"
            if source_data_manifest
            else ""
        )
        dataset_rows.append(
            {
                "dataset": item.get("dataset_id", ""),
                "dataset_name": item.get("dataset_name", ""),
                "gpt2_tokens": item.get("actual_gpt2_tokens", ""),
                "document_count": item.get("document_count", ""),
                "source": item.get("source", ""),
                "source_config": item.get("source_config", ""),
                "fallback_used": item.get("fallback_used", ""),
                "no_fallback_verified": item.get("no_fallback_verified", ""),
                "data_manifest": release_data_manifest,
                "evidence_level": "localmax_20m_token_sample",
            }
        )
    write_csv(
        TABLES_DIR / "localmax_dataset_summary_release.csv",
        [
            "dataset",
            "dataset_name",
            "gpt2_tokens",
            "document_count",
            "source",
            "source_config",
            "fallback_used",
            "no_fallback_verified",
            "data_manifest",
            "evidence_level",
        ],
        dataset_rows,
    )

    training_report = _load_json(ROOT / "artifacts" / "reports" / "localmax_training_strengthened_report.json")
    training_rows = []
    for (dataset, method), rows in sorted(grouped.items()):
        training_rows.append(
            {
                "dataset": dataset,
                "method": method,
                "completed_runs": len(rows),
                "model_scale": "small",
                "parameter_count": training_report.get("parameter_count", ""),
                "min_steps_completed": min(_int(row["steps_completed"]) for row in rows),
                "min_tokens_seen": min(_int(row["tokens_seen"]) for row in rows),
                "context_length": training_report.get("context_length", ""),
                "validation_token_sample_cap": training_report.get("validation_token_sample_cap", ""),
                "checkpoint_policy": "manifest_metrics_and_fingerprints_only",
                "evidence_level": "strengthened_small_model_training",
            }
        )
    write_csv(
        TABLES_DIR / "localmax_training_summary_release.csv",
        [
            "dataset",
            "method",
            "completed_runs",
            "model_scale",
            "parameter_count",
            "min_steps_completed",
            "min_tokens_seen",
            "context_length",
            "validation_token_sample_cap",
            "checkpoint_policy",
            "evidence_level",
        ],
        training_rows,
    )

    statistical_rows = _read_csv(EVALUATION_DIR / "statistical_tests.csv")
    stat_release = [
        {
            "dataset": row.get("dataset_id", ""),
            "comparison": row.get("comparison", ""),
            "test_name": row.get("test_name", ""),
            "n_seeds": row.get("n_seeds", ""),
            "mean_paired_loss_improvement": row.get("mean_paired_loss_improvement", ""),
            "ci_low": row.get("ci_low", ""),
            "ci_high": row.get("ci_high", ""),
            "ci_crosses_zero": row.get("ci_crosses_zero", ""),
            "improvement_claim_allowed": row.get("improvement_claim_allowed", "False"),
            "metric_for_comparison": row.get("metric_for_comparison", "valid_loss"),
        }
        for row in statistical_rows
    ]
    write_csv(
        TABLES_DIR / "localmax_statistical_summary_release.csv",
        [
            "dataset",
            "comparison",
            "test_name",
            "n_seeds",
            "mean_paired_loss_improvement",
            "ci_low",
            "ci_high",
            "ci_crosses_zero",
            "improvement_claim_allowed",
            "metric_for_comparison",
        ],
        stat_release,
    )

    claim_rows = [
        {
            "claim_id": "localmax_minimal_training_evidence_released",
            "allowed": "True",
            "evidence_link": "artifacts/localmax_release/tables/localmax_main_results_release.csv",
            "reason": "24 registry-backed strengthened small-model runs are present.",
        },
        {
            "claim_id": "urd_fixed_wins_over_raw",
            "allowed": "False",
            "evidence_link": "artifacts/localmax_release/tables/localmax_statistical_summary_release.csv",
            "reason": "URD evidence is mixed and confidence intervals do not support an improvement claim.",
        },
        {
            "claim_id": "ppl_improvement",
            "allowed": "False",
            "evidence_link": "artifacts/localmax_release/tables/localmax_main_results_release.csv",
            "reason": "PPL is clipped in the current run and is not comparable.",
        },
        {
            "claim_id": "level3_completed",
            "allowed": "False",
            "evidence_link": "docs/LOCALMAX_LIMITATIONS.md",
            "reason": "Cloud-scale data, true medium runs, selected large-lite runs, and official downstream evaluation are absent.",
        },
        {
            "claim_id": "ccf_b_level_readiness",
            "allowed": "False",
            "evidence_link": "docs/LOCALMAX_FUTURE_CLOUD_LEVEL3.md",
            "reason": "This release is a local minimal training-evidence artifact, not a completed conference-level benchmark.",
        },
    ]
    write_csv(
        TABLES_DIR / "localmax_claim_audit_release.csv",
        ["claim_id", "allowed", "evidence_link", "reason"],
        claim_rows,
    )

    table_hashes = {
        _release_path(path): sha256_file(path)
        for path in sorted(TABLES_DIR.glob("*.csv"))
    }
    payload = {
        "step": "step10C_localmax_release_freeze",
        "stage": "release_tables",
        "status": "completed" if not blocking else "completed_with_failures",
        "completed": not blocking,
        "frozen_release_timestamp": FROZEN_RELEASE_TIMESTAMP,
        "generated_at_runtime": False,
        "current_readiness": CURRENT_READINESS,
        "main_release_rows": len(main_rows),
        "bundle_scope": "standalone_metadata_bundle",
        "standalone_bundle": True,
        "metadata_and_metrics_included": True,
        "localmax_tables_finalized": not blocking,
        "historical_results_modified": not protected_hashes_unchanged(),
        "protected_hashes": protected_hashes(),
        "table_hashes": table_hashes,
        "blocking_failures": blocking,
    }
    _write_report(payload)
    if blocking:
        raise SystemExit("LocalMax release table generation failed.\n" + "\n".join(blocking))
    return payload


def main() -> None:
    payload = build_release_tables()
    print(json.dumps({"localmax_release_tables_ready": payload["completed"], "main_release_rows": payload["main_release_rows"]}))


if __name__ == "__main__":
    main()
