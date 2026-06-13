from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import json

from experiment_utils import root


REQUIRED_CATEGORIES = [
    "allowed_current_claims",
    "disallowed_current_claims",
    "protocol_only_claims",
    "future_level3_claims",
    "historical_result_claims",
    "negative_result_claims",
    "urd_claims",
    "baseline_claims",
    "dataset_scale_claims",
    "model_scale_claims",
    "evaluation_claims",
    "mechanism_claims",
    "ccf_level_claims",
]


def main() -> None:
    md_path = root / "docs" / "claim_map_level3.md"
    json_path = root / "artifacts" / "claim_map" / "claim_map_level3.json"
    errors = []
    if not md_path.exists():
        errors.append("missing docs/claim_map_level3.md")
    if not json_path.exists():
        errors.append("missing artifacts/claim_map/claim_map_level3.json")
    payload = {}
    if json_path.exists():
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    for category in REQUIRED_CATEGORIES:
        if category not in payload:
            errors.append(f"claim map missing category: {category}")
    if payload.get("current_readiness") != "LEVEL3_PIPELINE_READY":
        errors.append("claim map must keep current_readiness=LEVEL3_PIPELINE_READY")
    if payload.get("level3_completed_artifact") is not False:
        errors.append("claim map must keep level3_completed_artifact=false")
    if errors:
        raise SystemExit("Claim map check failed.\n" + "\n".join(errors))
    print("Claim map check: ok")


if __name__ == "__main__":
    main()

