from __future__ import annotations

import argparse

from execution_utils import environment_report, load_config, protected_hashes, utc_now, write_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or block Step 10B rehearsal honestly.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = load_config(args.config)
    env = environment_report()
    blocking = []
    if not env:
        blocking.append("Environment report missing; run check_heavy_environment.py first.")
    elif env.get("heavy_execution_feasible") is not True:
        blocking.extend(env.get("blocking_failures") or ["Heavy environment is not feasible."])
    payload = {
        "step": "step10B_level3_heavy_execution",
        "stage": "rehearsal",
        "status": "blocked" if blocking else "not_started",
        "completed": False,
        "rehearsal_completed": False,
        "target_bpe_tokens": int(config.get("target_bpe_tokens", 0)),
        "actual_bpe_tokens": 0,
        "evidence_level": "rehearsal_blocked" if blocking else "rehearsal_not_started",
        "level3_main_evidence": False,
        "write_to_level3_main_table": False,
        "heavy_execution_completed": False,
        "level3_completed_artifact": False,
        "main_results_modified": False,
        "historical_results_modified": False,
        "blocking_failures": blocking or ["Rehearsal implementation requires confirmed heavy environment and explicit execution window."],
        "fallbacks_used": [],
        "created_at": utc_now(),
        "protected_hashes": protected_hashes(),
    }
    write_report(payload, "step10B_rehearsal_report", "Step 10B Rehearsal Report")
    print(f"Step 10B rehearsal: {payload['status']}")


if __name__ == "__main__":
    main()

