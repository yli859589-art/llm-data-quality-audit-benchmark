from __future__ import annotations

import argparse
import json
import math
from typing import Any

from localmax_v2_utils import (
    ROOT,
    V2_FILTERS,
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
    risky = sum(lowered.count(term) for term in [" violence ", " hate ", " porn ", " kill ", " blood "])
    urlish = lowered.count("http://") + lowered.count("https://")
    return min(1.0, 0.05 * risky + 0.02 * urlish)


def _diversity_score(text: str) -> float:
    words = text.casefold().split()
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def _utility_score(token_count: int) -> float:
    return min(1.0, math.log1p(max(token_count, 1)) / math.log1p(2048))


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


def _decisions(method: str, docs: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    scored: list[tuple[float, str]] = []
    for doc in docs:
        text = str(doc.get("text", ""))
        token_count = int(doc.get("gpt2_tokens", 0))
        risk = _risk_score(text)
        diversity = _diversity_score(text)
        utility = _utility_score(token_count)
        score = utility + 0.25 * diversity - 0.5 * risk
        keep = True
        reason = "kept"
        if method == "exact_dedup":
            key = _normalize(text)
            keep = key not in seen
            seen.add(key)
            reason = "first_exact_normalized_text" if keep else "duplicate_exact_normalized_text"
        elif method == "length_filter":
            policy = config.get("length_filter", {})
            keep = int(policy.get("min_gpt2_tokens", 32)) <= token_count <= int(policy.get("max_gpt2_tokens", 2048))
            reason = "within_length_bounds" if keep else "outside_length_bounds"
        elif method == "urd_fixed":
            scored.append((score, str(doc["id"])))
            reason = "urd_score_ranked"
        rows.append(
            {
                "id": str(doc["id"]),
                "gpt2_tokens": token_count,
                "risk": risk,
                "diversity": diversity,
                "utility": utility,
                "score": score,
                "keep": keep,
                "reason": reason,
            }
        )
    if method == "urd_fixed":
        target_keep_rate = float(config.get("urd_fixed", {}).get("target_keep_rate", 0.9))
        keep_n = max(1, int(len(scored) * target_keep_rate))
        keep_ids = {doc_id for _, doc_id in sorted(scored, reverse=True)[:keep_n]}
        for row in rows:
            row["keep"] = row["id"] in keep_ids
            row["reason"] = "top_urd_fixed_score" if row["keep"] else "below_urd_fixed_cutoff"
    return rows


def _existing_ready(dataset_id: str, method: str) -> dict[str, Any] | None:
    manifest_path = V2_FILTERS / dataset_id / method / "filter_manifest.json"
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
    output_dir = V2_FILTERS / dataset_id / method
    manifest = load_json(ROOT / dataset["manifest_path"])
    docs = _load_train_docs(manifest)
    decisions = _decisions(method, docs, config)
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
        "step": "step10B_localmax_v2",
        "scope": "localmax_v2",
        "smoke_only": False,
        "protocol_only": False,
        "completed": True,
        "level3_filter": False,
        "dataset_id": dataset_id,
        "method_name": method,
        "method_family": "baseline" if method in {"raw", "exact_dedup", "length_filter"} else "candidate_method",
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
    parser.add_argument("--config", default="configs/localmax_v2/filter_matrix.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    data_report = load_json(ROOT / "artifacts" / "reports" / "localmax_v2_data_report.json")
    datasets = data_report.get("nontrivial_datasets", [])
    blocking: list[str] = []
    if len(datasets) < int(config["minimum_datasets"]):
        blocking.append("LocalMax V2 filters require two >=100M-token datasets.")
    rows: list[dict[str, Any]] = []
    if not blocking:
        for dataset in datasets[: int(config["minimum_datasets"])]:
            for method in config["required_methods"]:
                rows.append(_run_one(dataset, str(method), config))
    expected = int(config["minimum_datasets"]) * int(config["minimum_methods"])
    ready = len([row for row in rows if row["completed"]]) >= expected
    if not ready and not blocking:
        blocking.append(f"Filter matrix completed {len(rows)}/{expected}.")
    report = status_payload(
        "filters",
        ready,
        blocking,
        {
            "status": "completed" if ready else "blocked",
            "current_readiness": "LOCAL_MAX_V2_FILTERS_COMPLETED" if ready else "LOCAL_MAX_V2_PARTIAL_WITH_REAL_EVIDENCE",
            "localmax_v2_filters_ready": ready,
            "filter_results": rows,
            "datasets_completed": sorted(set(row["dataset_id"] for row in rows)),
            "methods_completed": sorted(set(row["method_name"] for row in rows)),
            "minimum_matrix": "2 datasets x 4 methods",
            "recommended_next_step": "benchmark_training_throughput" if ready else "continue_filter_execution",
        },
    )
    write_report(report, "localmax_v2_filter_report", "LocalMax V2 Filter Report")
    print(json.dumps({"localmax_v2_filters_ready": ready, "completed_filters": len(rows)}))
    if not ready:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
