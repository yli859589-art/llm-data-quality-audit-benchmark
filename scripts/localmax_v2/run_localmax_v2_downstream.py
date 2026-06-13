from __future__ import annotations

import argparse
import json

from localmax_v2_utils import V2_DOWNSTREAM, load_config, status_payload, write_csv, write_json, write_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/localmax_v2/downstream_matrix.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    rows = []
    for name in config["benchmarks"]:
        rows.append(
            {
                "benchmark": name,
                "requested_examples": config["examples_per_benchmark"],
                "local_downstream_subset": True,
                "official_full_downstream": False,
                "status": "unavailable",
                "reason": "Current local decoder-LM artifacts do not include a calibrated downstream harness/checkpoint interface for this benchmark.",
                "score": "",
                "claim_allowed": False,
            }
        )
    V2_DOWNSTREAM.mkdir(parents=True, exist_ok=True)
    write_csv(
        V2_DOWNSTREAM / "downstream_subset.csv",
        ["benchmark", "requested_examples", "local_downstream_subset", "official_full_downstream", "status", "reason", "score", "claim_allowed"],
        rows,
    )
    manifest = {
        "step": "step10B_localmax_v2",
        "scope": "localmax_v2_downstream",
        "completed": False,
        "local_downstream_subset": True,
        "official_full_downstream": False,
        "downstream_subset": "artifacts/localmax_v2_downstream/downstream_subset.csv",
        "claim_allowed": False,
    }
    write_json(V2_DOWNSTREAM / "downstream_manifest.json", manifest)
    report = status_payload(
        "downstream",
        True,
        [],
        {
            "status": "completed_with_unavailable_downstream",
            "current_readiness": "LOCAL_MAX_V2_DOWNSTREAM_RECORDED",
            "local_downstream_subset": True,
            "official_full_downstream": False,
            "downstream_completed": False,
            "downstream_rows": len(rows),
            "claim_allowed": False,
            "notes": [
                "Downstream subset availability was recorded honestly.",
                "No official downstream completion claim is made.",
            ],
        },
    )
    write_report(report, "localmax_v2_downstream_report", "LocalMax V2 Downstream Subset Report")
    print(json.dumps({"downstream_recorded": True, "official_full_downstream": False, "rows": len(rows)}))


if __name__ == "__main__":
    main()
