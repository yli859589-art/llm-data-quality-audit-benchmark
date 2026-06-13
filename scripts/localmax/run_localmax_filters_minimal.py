from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from localmax_utils import (
    LOCALMAX_FILTERS,
    REPORTS,
    ROOT,
    load_json,
    rel,
    sha256_file,
    status_payload,
    utc_now,
    write_json,
    write_report,
)


def _load_config(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _risk_score(text: str) -> float:
    lowered = text.casefold()
    risky = sum(lowered.count(term) for term in [" violence ", " hate ", " porn ", " kill ", " blood "])
    urlish = lowered.count("http://") + lowered.count("https://")
    return min(1.0, 0.05 * risky + 0.02 * urlish)


def _diversity_score(text: str) -> float:
    words = text.casefold().split()
    if not words:
        return 0.0
    return len(set(words)) / max(len(words), 1)


def _utility_score(token_count: int) -> float:
    return min(1.0, math.log1p(max(token_count, 1)) / math.log1p(1024))


def _decide(method: str, docs: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = []
    seen: set[str] = set()
    scored = []
    for doc in docs:
        text = str(doc["text"])
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
            keep = int(policy.get("min_gpt2_tokens", 64)) <= token_count <= int(policy.get("max_gpt2_tokens", 2048))
            reason = "within_length_bounds" if keep else "outside_length_bounds"
        elif method == "urd_fixed":
            scored.append((score, doc["id"]))
            reason = "urd_score_ranked"
        decisions.append(
            {
                "id": doc["id"],
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
        for row in decisions:
            row["keep"] = row["id"] in keep_ids
            row["reason"] = "top_urd_fixed_score" if row["keep"] else "below_urd_fixed_cutoff"
    return decisions


def _run_one(dataset: dict[str, Any], method: str, config: dict[str, Any]) -> dict[str, Any]:
    dataset_id = dataset["dataset_id"]
    output_dir = LOCALMAX_FILTERS / dataset_id / method
    existing_manifest = output_dir / "filter_manifest.json"
    if existing_manifest.exists():
        payload = load_json(existing_manifest)
        if payload.get("completed") is True and (ROOT / payload.get("selected_doc_ids_path", "")).exists():
            return {
                "dataset_id": dataset_id,
                "method_name": method,
                "filter_manifest_path": rel(existing_manifest),
                "document_keep_rate": payload.get("document_keep_rate", 0.0),
                "token_keep_rate": payload.get("token_keep_rate", 0.0),
                "kept_documents": payload.get("kept_documents", 0),
                "kept_gpt2_tokens": payload.get("kept_gpt2_tokens", 0),
                "completed": True,
                "reused_existing_artifact": True,
            }
    manifest = load_json(ROOT / dataset["manifest_path"])
    docs = _read_jsonl(ROOT / manifest["split_paths"]["train"])
    decisions = _decide(method, docs, config)
    kept = [row for row in decisions if row["keep"]]
    selected_rows = [{"id": row["id"]} for row in kept]
    _write_jsonl(output_dir / "selected_doc_ids.jsonl", selected_rows)
    _write_jsonl(output_dir / "scores_or_decisions.jsonl", decisions)
    input_tokens = sum(int(row.get("gpt2_tokens", 0)) for row in decisions)
    kept_tokens = sum(int(row.get("gpt2_tokens", 0)) for row in kept)
    keep_rate = len(kept) / max(len(decisions), 1)
    token_keep_rate = kept_tokens / max(input_tokens, 1)
    risk_values = [float(row["risk"]) for row in kept]
    diversity_values = [float(row["diversity"]) for row in kept]
    keep_rate_report = {
        "dataset_id": dataset_id,
        "method_name": method,
        "input_documents": len(decisions),
        "kept_documents": len(kept),
        "input_gpt2_tokens": input_tokens,
        "kept_gpt2_tokens": kept_tokens,
        "document_keep_rate": keep_rate,
        "token_keep_rate": token_keep_rate,
        "created_at": utc_now(),
    }
    risk_report = {
        "dataset_id": dataset_id,
        "method_name": method,
        "mean_risk": sum(risk_values) / max(len(risk_values), 1),
        "max_risk": max(risk_values) if risk_values else 0.0,
        "created_at": utc_now(),
    }
    diversity_report = {
        "dataset_id": dataset_id,
        "method_name": method,
        "mean_diversity": sum(diversity_values) / max(len(diversity_values), 1),
        "created_at": utc_now(),
    }
    cost_report = {
        "dataset_id": dataset_id,
        "method_name": method,
        "filter_cost_units": len(decisions),
        "cost_proxy": "documents_scored",
        "created_at": utc_now(),
    }
    manifest_payload = {
        "step": "step10B_localmax_execution_fix",
        "scope": "localmax_minimal",
        "smoke_only": False,
        "protocol_only": False,
        "completed": True,
        "level3_filter": False,
        "dataset_id": dataset_id,
        "method_name": method,
        "dataset_manifest": dataset["manifest_path"],
        "tokenizer_manifest": "artifacts/localmax_tokenizers/gpt2/tokenizer_manifest.json",
        "selected_doc_ids_path": rel(output_dir / "selected_doc_ids.jsonl"),
        "scores_or_decisions_path": rel(output_dir / "scores_or_decisions.jsonl"),
        "document_keep_rate": keep_rate,
        "token_keep_rate": token_keep_rate,
        "input_documents": len(decisions),
        "kept_documents": len(kept),
        "input_gpt2_tokens": input_tokens,
        "kept_gpt2_tokens": kept_tokens,
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
        "document_keep_rate": keep_rate,
        "token_keep_rate": token_keep_rate,
        "kept_documents": len(kept),
        "kept_gpt2_tokens": kept_tokens,
        "completed": True,
        "reused_existing_artifact": False,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax/filter_matrix_minimal.yaml")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = _load_config(args.config)
    data_report = load_json(REPORTS / "localmax_data_report.json")
    datasets = data_report.get("nontrivial_datasets", [])
    blocking = []
    rows = []
    if len(datasets) < int(config["minimum_datasets"]):
        blocking.append("LocalMax minimal filter requires two nontrivial >=20M-token datasets.")
    else:
        for dataset in datasets[: int(config["minimum_datasets"])]:
            for method in config["required_methods"]:
                rows.append(_run_one(dataset, method, config))
    ready = len(rows) >= int(config["minimum_datasets"]) * int(config["minimum_methods"])
    if not ready and not blocking:
        blocking.append("Filter matrix did not complete the required 2 datasets x 4 methods.")
    report = status_payload(
        "filter",
        ready,
        blocking,
        {
            "step": "step10B_localmax_execution_fix",
            "status": "completed" if ready else "blocked",
            "localmax_filters_ready": ready,
            "filter_results": rows,
            "datasets_completed": sorted(set(row["dataset_id"] for row in rows)),
            "methods_completed": sorted(set(row["method_name"] for row in rows)),
            "minimum_matrix": "2 datasets x 4 methods",
            "level3_filter": False,
            "recommended_next_step": "run_localmax_minimal_training" if ready else "continue_filter_execution",
        },
    )
    write_report(report, "localmax_filter_report", "LocalMax Minimal Filter Report")
    print(json.dumps({"localmax_filters_ready": ready, "completed_filters": len(rows)}))


if __name__ == "__main__":
    main()
