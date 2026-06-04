from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from course_project_suite.llm_benchmark.quality import QualityWeights
from data.splitter import deterministic_split, split_hashes


def _config_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_frozen_protocol(
    *,
    dataset_key: str,
    documents: list[str],
    seed: int,
    output_path: Path,
    threshold: float = 0.58,
    weights: QualityWeights | None = None,
) -> dict[str, Any]:
    weights = weights or QualityWeights()
    splits = deterministic_split(documents, seed=seed)
    protocol = {
        "protocol_name": f"hdqspp_frozen_{dataset_key}",
        "dataset_key": dataset_key,
        "seed": seed,
        "threshold": threshold,
        "quality_weights": asdict(weights),
        "split_hashes": split_hashes(splits),
        "selection_rule": "Tune threshold on train/dev only; evaluate held-out test once.",
        "no_test_leakage": True,
        "frozen": True,
        "status": "smoke_frozen_protocol" if len(documents) < 1000 else "paper_candidate",
    }
    protocol["config_sha256"] = _config_hash(protocol)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(protocol, indent=2, sort_keys=True), encoding="utf-8")
    return protocol
