from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from artifacts_v2.canonical_io import write_canonical_json, write_canonical_text

CONFIG_ROOT = ROOT / "configs" / "level3"

CONFIG_FILES = [
    "data_matrix.yaml",
    "data_sources.yaml",
    "token_budget.yaml",
    "tokenizers.yaml",
    "filter_matrix.yaml",
    "model_matrix.yaml",
    "training_matrix.yaml",
    "evaluation_matrix.yaml",
    "mechanism_matrix.yaml",
    "statistics_protocol.yaml",
    "compute_budget.yaml",
    "artifact_paths.yaml",
    "claim_boundary.yaml",
]

PROTECTED_RESULT_FILES = [
    "artifacts/tables/main_results.csv",
    "artifacts/stats/main_results.csv",
    "artifacts/cross_dataset/cross_dataset_results.csv",
    "artifacts/runs/run_registry.jsonl",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_config(filename: str) -> dict[str, Any]:
    path = CONFIG_ROOT / filename
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{filename} must contain a JSON object")
    return payload


def load_all_configs() -> dict[str, dict[str, Any]]:
    return {filename: load_config(filename) for filename in CONFIG_FILES}


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256_file(path: Path) -> str:
    import hashlib

    data = path.read_bytes()
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        canonical = data
    else:
        canonical = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", "\r\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest().upper()


def protected_hashes() -> dict[str, str]:
    hashes: dict[str, str] = {}
    for item in PROTECTED_RESULT_FILES:
        path = ROOT / item
        if path.exists():
            hashes[item] = sha256_file(path)
    return hashes


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def validate_protocol() -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    missing = [name for name in CONFIG_FILES if not (CONFIG_ROOT / name).exists()]
    errors.extend(f"missing configs/level3/{name}" for name in missing)
    configs: dict[str, dict[str, Any]] = {}
    if not missing:
        try:
            configs = load_all_configs()
        except Exception as exc:  # pragma: no cover - defensive report path
            errors.append(f"failed to parse level3 configs: {exc}")

    for name, payload in configs.items():
        _require(errors, payload.get("step") == "step10A_level3_heavy_protocol_freeze", f"{name} has wrong step")
        _require(errors, payload.get("protocol_only") is True, f"{name} must set protocol_only=true")
        _require(errors, payload.get("completed") is False, f"{name} must set completed=false")

    if configs:
        data = configs["data_matrix.yaml"]
        required_datasets = [item for item in data.get("datasets", []) if item.get("required") is True]
        _require(errors, data.get("token_count_type") == "tokenizer_specific_bpe_tokens", "data matrix must use tokenizer-specific BPE counts")
        _require(errors, len(required_datasets) >= 3, "data matrix must require at least three datasets")
        _require(errors, all(int(item.get("target_bpe_tokens", 0)) >= 500_000_000 for item in required_datasets), "each required dataset must target at least 500M BPE tokens")
        _require(errors, all(item.get("no_fallback_required") is True for item in required_datasets), "required datasets must forbid fallback")
        _require(errors, all(item.get("split_integrity_required") is True for item in required_datasets), "required datasets must require split integrity")
        _require(errors, int(data.get("strong_target", {}).get("tokens_per_dataset", 0)) >= 1_000_000_000, "strong target must preserve 1B-token option")

        sources = configs["data_sources.yaml"]
        _require(errors, all(item.get("download_in_step10A") is False for item in sources.get("sources", [])), "Step 10A data sources must not download data")

        budget = configs["token_budget.yaml"]
        _require(errors, budget.get("counter_type") == "tokenizer_specific_bpe_tokens", "token budget must use tokenizer-specific BPE tokens")
        _require(errors, int(budget.get("minimum", {}).get("tokens_per_dataset", 0)) >= 500_000_000, "minimum token budget must be at least 500M per dataset")
        _require(errors, "whitespace_proxy" in budget.get("disallowed_counters", []), "whitespace proxy counter must be disallowed")

        tokenizer_cfg = configs["tokenizers.yaml"]
        tokenizers = {item.get("tokenizer_id"): item for item in tokenizer_cfg.get("tokenizers", [])}
        for tokenizer_id in ["gpt2", "bpe16k", "bpe32k"]:
            _require(errors, tokenizers.get(tokenizer_id, {}).get("mainline_allowed") is True, f"{tokenizer_id} must be mainline-allowed")
        _require(errors, tokenizers.get("char_legacy", {}).get("mainline_allowed") is False, "char tokenizer must stay legacy/smoke only")
        _require(errors, tokenizers.get("lightweight_bpe_smoke", {}).get("mainline_allowed") is False, "lightweight BPE smoke tokenizer must not be mainline")

        filters = configs["filter_matrix.yaml"]
        method_ids = {item.get("method_id") for item in filters.get("methods", [])}
        required_methods = {
            "raw",
            "random_same_keep_rate",
            "exact_dedup",
            "minhash_near_dedup",
            "length_filter",
            "c4_style_heuristic_proxy",
            "gopher_style_heuristic_proxy",
            "ccnet_style_proxy",
            "perplexity_filter",
            "classifier_quality_proxy",
            "embedding_diversity_selector",
            "hdqspp_historical",
            "urd_fixed",
            "urd_pareto",
            "urd_ablation_no_utility",
            "urd_ablation_no_risk",
            "urd_ablation_no_diversity",
            "urd_ablation_no_shift",
            "urd_ablation_no_cost",
        }
        _require(errors, required_methods.issubset(method_ids), "filter matrix is missing required baselines or URD ablations")
        _require(errors, filters.get("keep_rate_policy") == "matched_keep_rate_per_dataset_tokenizer_and_method_family", "filter matrix must require matched keep-rate fairness")

        models = configs["model_matrix.yaml"]
        model_ids = {item.get("scale_id") for item in models.get("model_scales", [])}
        _require(errors, {"small", "medium", "large_lite"}.issubset(model_ids), "model matrix must include small, medium, and large_lite")
        _require(errors, models.get("completion_rules", {}).get("small_only_is_not_level3_completed") is True, "small-only completion must be blocked")
        _require(errors, models.get("completion_rules", {}).get("medium_required_for_level3") is True, "medium model must be required")

        training = configs["training_matrix.yaml"]
        default_seeds = training.get("minimum_requirements", {}).get("default_seeds", [])
        _require(errors, len(default_seeds) >= 3, "training protocol must require at least three seeds for main runs")
        _require(errors, training.get("minimum_requirements", {}).get("medium_completed") is True, "training protocol must require medium completion")
        _require(errors, all(int(item.get("tokens", 0)) >= 500_000_000 for item in training.get("matrix", []) if item.get("dataset_id") != "best_subset"), "training rows must preserve the 500M floor")
        _require(errors, "write_ppl_result" in training.get("forbidden_in_step10A", []), "Step 10A must forbid writing PPL results")

        evaluation = configs["evaluation_matrix.yaml"]
        metrics = set(evaluation.get("metrics", []))
        _require(errors, {"lm_validation_ppl", "downstream", "risk", "diversity", "cost", "pareto", "statistics"}.issubset(metrics), "evaluation metrics are incomplete")
        required_downstream = [item for item in evaluation.get("downstream_benchmarks", []) if item.get("required")]
        _require(errors, len(required_downstream) >= int(evaluation.get("minimum_downstream_benchmarks", 0)), "downstream protocol must require enough benchmarks")
        _require(errors, evaluation.get("official_downstream_completed_in_step10A") is False, "Step 10A must not mark downstream completed")

        mechanisms = set(configs["mechanism_matrix.yaml"].get("analyses", []))
        _require(errors, {"proxy_utility_mismatch", "overfiltering", "diversity_loss", "domain_shift", "rank_stability", "tokenizer_sensitivity", "scale_trend", "failure_taxonomy", "negative_result_analysis"}.issubset(mechanisms), "mechanism matrix is incomplete")

        statistics = configs["statistics_protocol.yaml"]
        rules = statistics.get("rules", {})
        _require(errors, rules.get("n_equals_1_significance_claim_allowed") is False, "n=1 significance must be forbidden")
        _require(errors, rules.get("ci_crosses_zero_blocks_improvement_claim") is True, "CI crossing zero must block improvement claims")

        compute = configs["compute_budget.yaml"]
        _require(errors, compute.get("fallback_cannot_preserve_completed_artifact_unless_minimum_thresholds_hold") is True, "fallback policy must block completed artifact if floors fail")

        paths = configs["artifact_paths.yaml"]
        named_outputs = paths.get("named_outputs", {})
        for key in ["main_table", "baseline_report", "urd_report", "downstream_report", "mechanism_report", "final_release_zip"]:
            _require(errors, key in named_outputs, f"artifact path spec missing {key}")
        for value in list(paths.get("artifact_roots", {}).values()) + list(named_outputs.values()):
            _require(errors, not Path(value).is_absolute(), f"artifact path must be relative: {value}")

        claim = configs["claim_boundary.yaml"]
        _require(errors, claim.get("current_readiness") == "LEVEL3_PIPELINE_READY", "claim boundary must keep LEVEL3_PIPELINE_READY")
        _require(errors, claim.get("level3_completed_artifact") is False, "claim boundary must keep level3_completed_artifact=false")
        _require(errors, "Level 3 completed." in claim.get("disallowed_current_claims", []), "claim boundary must disallow Level 3 completed claim")

    return {
        "status": "passed" if not errors else "failed",
        "checked_at": utc_now(),
        "step": "step10A_level3_heavy_protocol_freeze",
        "protocol_only": True,
        "completed": False,
        "config_root": rel(CONFIG_ROOT),
        "config_files": [f"configs/level3/{name}" for name in CONFIG_FILES],
        "errors": errors,
        "warnings": warnings,
        "protected_hashes": protected_hashes(),
    }


def write_report(payload: dict[str, Any], json_path: Path, md_path: Path, title: str) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json(json_path, payload)
    lines = [
        f"# {title}",
        "",
        f"- Status: `{payload.get('status')}`",
        f"- Step: `{payload.get('step')}`",
        f"- Protocol only: `{payload.get('protocol_only')}`",
        f"- Completed heavy evidence: `{payload.get('completed')}`",
        "",
        "## Errors",
        "",
    ]
    errors = payload.get("errors") or []
    lines.extend([f"- {item}" for item in errors] if errors else ["- none"])
    warnings = payload.get("warnings") or []
    lines.extend(["", "## Warnings", ""])
    lines.extend([f"- {item}" for item in warnings] if warnings else ["- none"])
    if payload.get("protected_hashes"):
        lines.extend(["", "## Protected Hashes", "", "| File | SHA256 |", "|---|---|"])
        for file_path, digest in payload["protected_hashes"].items():
            lines.append(f"| `{file_path}` | `{digest}` |")
    write_canonical_text(md_path, "\n".join(lines))
