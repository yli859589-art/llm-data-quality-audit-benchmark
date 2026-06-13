from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import string
from typing import Any

from ccfc_utils import (
    CCFC_FILTERS,
    ROOT,
    iter_jsonl_any,
    load_config,
    load_json,
    rel,
    status_payload,
    utc_now,
    write_json,
    write_jsonl_gz,
    write_report,
)


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _risk_score(text: str) -> float:
    lowered = f" {text.casefold()} "
    risky = sum(lowered.count(term) for term in [" violence ", " hate ", " porn ", " kill ", " blood ", " casino ", " viagra "])
    urlish = lowered.count("http://") + lowered.count("https://")
    return min(1.0, 0.05 * risky + 0.02 * urlish)


def _diversity_score(text: str) -> float:
    words = text.casefold().split()
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def _utility_score(token_count: int) -> float:
    return min(1.0, math.log1p(max(token_count, 1)) / math.log1p(2048))


def _symbol_fraction(text: str) -> float:
    if not text:
        return 1.0
    symbol_chars = sum(1 for char in text if not char.isalnum() and not char.isspace())
    return symbol_chars / max(1, len(text))


def _alpha_fraction(text: str) -> float:
    if not text:
        return 0.0
    alpha_chars = sum(1 for char in text if char.isalpha())
    return alpha_chars / max(1, len(text))


def _perplexity_proxy_score(text: str, token_count: int) -> float:
    words = text.casefold().split()
    if not words:
        return float("inf")
    repetition = 1.0 - (len(set(words)) / max(1, len(words)))
    punctuation = sum(1 for char in text if char in string.punctuation) / max(1, len(text))
    length_penalty = abs(math.log1p(token_count) - math.log1p(384)) / math.log1p(4096)
    digit_fraction = sum(1 for char in text if char.isdigit()) / max(1, len(text))
    return repetition + 0.8 * punctuation + 0.5 * digit_fraction + 0.35 * length_penalty


def _train_paths(manifest: dict[str, Any]) -> list[str]:
    value = manifest.get("split_paths", {}).get("train", [])
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)] if value else []


def _load_train_docs(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for rel_path in _train_paths(manifest):
        docs.extend(iter_jsonl_any(ROOT / rel_path))
    return docs


def _length_keep(token_count: int, config: dict[str, Any]) -> bool:
    policy = config.get("length_filter", {})
    return int(policy.get("min_gpt2_tokens", 32)) <= token_count <= int(policy.get("max_gpt2_tokens", 2048))


def _c4_quality_keep(text: str, token_count: int, config: dict[str, Any]) -> tuple[bool, str]:
    policy = config.get("c4_quality_filter", {})
    lowered = text.casefold()
    if token_count < int(policy.get("min_gpt2_tokens", 24)):
        return False, "too_short_c4_style"
    if token_count > int(policy.get("max_gpt2_tokens", 4096)):
        return False, "too_long_c4_style"
    if _symbol_fraction(text) > float(policy.get("max_symbol_fraction", 0.35)):
        return False, "symbol_fraction_too_high"
    if _alpha_fraction(text) < float(policy.get("min_alpha_fraction", 0.45)):
        return False, "alpha_fraction_too_low"
    for term in policy.get("blocked_terms", []):
        if str(term).casefold() in lowered:
            return False, "blocked_term"
    return True, "c4_style_quality_pass"


def _base_rows(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for doc in docs:
        text = str(doc.get("text", ""))
        token_count = int(doc.get("gpt2_tokens", 0))
        risk = _risk_score(text)
        diversity = _diversity_score(text)
        utility = _utility_score(token_count)
        rows.append(
            {
                "id": str(doc["id"]),
                "gpt2_tokens": token_count,
                "risk": risk,
                "diversity": diversity,
                "utility": utility,
                "perplexity_proxy": _perplexity_proxy_score(text, token_count),
                "text": text,
                "score": utility + 0.25 * diversity - 0.5 * risk,
                "keep": True,
                "reason": "kept",
            }
        )
    return rows


def _decisions(dataset_id: str, method: str, docs: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    rows = _base_rows(docs)
    if method == "raw":
        for row in rows:
            row["reason"] = "raw_keep_all"
    elif method == "exact_dedup":
        seen: set[str] = set()
        for row in rows:
            key = _normalize(row.pop("text"))
            row["keep"] = key not in seen
            seen.add(key)
            row["reason"] = "first_exact_normalized_text" if row["keep"] else "duplicate_exact_normalized_text"
        return rows
    elif method == "length_filter":
        for row in rows:
            row["keep"] = _length_keep(int(row["gpt2_tokens"]), config)
            row["reason"] = "within_length_bounds" if row["keep"] else "outside_length_bounds"
    elif method == "random_same_keep_rate":
        length_keep_n = sum(1 for row in rows if _length_keep(int(row["gpt2_tokens"]), config))
        seed_material = f"{dataset_id}:{config.get('random_same_keep_rate', {}).get('seed', 20260613)}"
        rng = random.Random(int(hashlib.sha256(seed_material.encode("utf-8")).hexdigest()[:12], 16))
        shuffled = [row["id"] for row in rows]
        rng.shuffle(shuffled)
        keep_ids = set(shuffled[:length_keep_n])
        for row in rows:
            row["keep"] = row["id"] in keep_ids
            row["reason"] = "random_same_keep_rate_selected" if row["keep"] else "random_same_keep_rate_rejected"
    elif method == "c4_quality_filter":
        for row in rows:
            keep, reason = _c4_quality_keep(row["text"], int(row["gpt2_tokens"]), config)
            row["keep"] = keep
            row["reason"] = reason
    elif method == "perplexity_proxy_filter":
        proxy_values = sorted(float(row["perplexity_proxy"]) for row in rows)
        policy = config.get("perplexity_proxy_filter", {})
        low_q = float(policy.get("low_surprisal_quantile", 0.05))
        high_q = float(policy.get("high_surprisal_quantile", 0.95))
        low = proxy_values[min(len(proxy_values) - 1, int(low_q * (len(proxy_values) - 1)))]
        high = proxy_values[min(len(proxy_values) - 1, int(high_q * (len(proxy_values) - 1)))]
        filtered = [row for row in rows if low <= float(row["perplexity_proxy"]) <= high]
        target_keep = int(len(rows) * float(policy.get("target_keep_rate", 0.75)))
        keep_ids = {row["id"] for row in sorted(filtered, key=lambda item: float(item["perplexity_proxy"]))[:target_keep]}
        for row in rows:
            row["keep"] = row["id"] in keep_ids
            row["reason"] = "low_perplexity_proxy_selected" if row["keep"] else "perplexity_proxy_rejected"
    elif method == "urd_fixed":
        target_keep_rate = float(config.get("urd_fixed", {}).get("target_keep_rate", 0.9))
        keep_n = max(1, int(len(rows) * target_keep_rate))
        keep_ids = {row["id"] for row in sorted(rows, key=lambda item: float(item["score"]), reverse=True)[:keep_n]}
        for row in rows:
            row["keep"] = row["id"] in keep_ids
            row["reason"] = "top_urd_fixed_score" if row["keep"] else "below_urd_fixed_cutoff"
    else:
        raise ValueError(f"Unknown CCF-C filter method: {method}")
    for row in rows:
        row.pop("text", None)
    return rows


def _existing_ready(dataset_id: str, method: str) -> dict[str, Any] | None:
    manifest_path = CCFC_FILTERS / dataset_id / method / "filter_manifest.json"
    if not manifest_path.exists():
        return None
    payload = load_json(manifest_path)
    if payload.get("completed") is True and (ROOT / str(payload.get("selected_doc_ids_path", ""))).exists():
        return {
            "dataset_id": dataset_id,
            "method_name": method,
            "filter_manifest_path": rel(manifest_path),
            "document_keep_rate": payload.get("document_keep_rate", 0.0),
            "token_keep_rate": payload.get("token_keep_rate", 0.0),
            "selected_gpt2_tokens": payload.get("selected_gpt2_tokens", 0),
            "source_data_tokens": payload.get("source_data_tokens", 0),
            "completed": True,
            "reused_existing_artifact": True,
        }
    return None


def _run_one(dataset: dict[str, Any], method: str, config: dict[str, Any]) -> dict[str, Any]:
    dataset_id = str(dataset["dataset_id"])
    existing = _existing_ready(dataset_id, method)
    if existing:
        return existing
    output_dir = CCFC_FILTERS / dataset_id / method
    manifest = load_json(ROOT / dataset["manifest_path"])
    docs = _load_train_docs(manifest)
    decisions = _decisions(dataset_id, method, docs, config)
    kept = [row for row in decisions if row["keep"]]
    selected_rows = [{"id": row["id"], "gpt2_tokens": row["gpt2_tokens"]} for row in kept]
    source_tokens = sum(int(row["gpt2_tokens"]) for row in decisions)
    selected_tokens = sum(int(row["gpt2_tokens"]) for row in kept)
    risks = [float(row["risk"]) for row in kept]
    diversities = [float(row["diversity"]) for row in kept]
    keep_rate_report = {
        "dataset_id": dataset_id,
        "method_name": method,
        "input_documents": len(decisions),
        "kept_documents": len(kept),
        "source_data_tokens": source_tokens,
        "selected_gpt2_tokens": selected_tokens,
        "document_keep_rate": len(kept) / max(1, len(decisions)),
        "token_keep_rate": selected_tokens / max(1, source_tokens),
        "created_at": utc_now(),
    }
    risk_report = {
        "dataset_id": dataset_id,
        "method_name": method,
        "mean_risk": sum(risks) / max(1, len(risks)),
        "max_risk": max(risks) if risks else 0.0,
        "created_at": utc_now(),
    }
    diversity_report = {
        "dataset_id": dataset_id,
        "method_name": method,
        "mean_diversity": sum(diversities) / max(1, len(diversities)),
        "created_at": utc_now(),
    }
    cost_report = {
        "dataset_id": dataset_id,
        "method_name": method,
        "filter_cost_units": len(decisions),
        "cost_proxy": "documents_scored",
        "created_at": utc_now(),
    }
    selected_path = output_dir / "selected_doc_ids.jsonl.gz"
    decisions_path = output_dir / "scores_or_decisions.jsonl.gz"
    write_jsonl_gz(selected_path, selected_rows)
    write_jsonl_gz(decisions_path, decisions)
    manifest_payload = {
        "step": "localmax_ccfc_strengthening",
        "scope": "ccfc_filter_matrix",
        "smoke_only": False,
        "protocol_only": False,
        "completed": True,
        "ccf_c_paper_claimed": False,
        "dataset_id": dataset_id,
        "method_name": method,
        "method_family": "baseline" if method != "urd_fixed" else "candidate_method",
        "dataset_manifest": dataset["manifest_path"],
        "tokenizer_manifest": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "selected_doc_ids_path": rel(selected_path),
        "scores_or_decisions_path": rel(decisions_path),
        "keep_rate_report": rel(output_dir / "keep_rate_report.json"),
        "risk_report": rel(output_dir / "risk_report.json"),
        "diversity_report": rel(output_dir / "diversity_report.json"),
        "cost_report": rel(output_dir / "cost_report.json"),
        "document_keep_rate": keep_rate_report["document_keep_rate"],
        "token_keep_rate": keep_rate_report["token_keep_rate"],
        "selected_gpt2_tokens": selected_tokens,
        "source_data_tokens": source_tokens,
        "input_documents": len(decisions),
        "kept_documents": len(kept),
        "created_at": utc_now(),
    }
    write_json(output_dir / "keep_rate_report.json", keep_rate_report)
    write_json(output_dir / "risk_report.json", risk_report)
    write_json(output_dir / "diversity_report.json", diversity_report)
    write_json(output_dir / "cost_report.json", cost_report)
    write_json(output_dir / "filter_manifest.json", manifest_payload)
    return {
        "dataset_id": dataset_id,
        "method_name": method,
        "filter_manifest_path": rel(output_dir / "filter_manifest.json"),
        "document_keep_rate": keep_rate_report["document_keep_rate"],
        "token_keep_rate": keep_rate_report["token_keep_rate"],
        "selected_gpt2_tokens": selected_tokens,
        "source_data_tokens": source_tokens,
        "completed": True,
        "reused_existing_artifact": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax_ccfc/filter_matrix.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    data_report = load_json(config["source_data_report"])
    datasets = data_report.get("nontrivial_datasets", [])
    blocking: list[str] = []
    if len(datasets) < int(config["minimum_datasets"]):
        blocking.append("CCF-C filter matrix requires two >=100M-token non-fallback datasets.")
    rows: list[dict[str, Any]] = []
    if not blocking:
        for dataset in datasets[: int(config["minimum_datasets"])]:
            for method in config["required_methods"]:
                rows.append(_run_one(dataset, str(method), config))
    expected = int(config["minimum_datasets"]) * int(config["minimum_methods"])
    ready = len([row for row in rows if row["completed"]]) >= expected
    if not ready and not blocking:
        blocking.append(f"CCF-C filter matrix completed {len(rows)}/{expected}.")
    report = status_payload(
        "filters",
        ready,
        blocking,
        {
            "status": "completed" if ready else "blocked",
            "current_readiness": "CCFC_FILTER_MATRIX_COMPLETED" if ready else "CCFC_PARTIAL_EVIDENCE",
            "ccfc_filters_ready": ready,
            "filter_results": rows,
            "datasets_completed": sorted(set(row["dataset_id"] for row in rows)),
            "methods_completed": sorted(set(row["method_name"] for row in rows)),
            "minimum_matrix": "2 datasets x 7 methods",
            "recommended_next_step": "run_ccfc_training" if ready else "continue_filter_execution",
        },
    )
    write_report(report, "localmax_ccfc_filter_report", "LocalMax CCF-C Filter Matrix Report")
    print(json.dumps({"ccfc_filters_ready": ready, "completed_filters": len(rows)}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
