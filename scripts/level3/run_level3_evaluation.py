from __future__ import annotations

import argparse

from execution_utils import blocked_stage_report, stage_blocking_from_environment, stage_blocking_from_rehearsal, write_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Level 3 evaluation or write an honest blocked report.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def main() -> None:
    _parse_args()
    blocking = stage_blocking_from_environment() or stage_blocking_from_rehearsal()
    payload = blocked_stage_report(
        "evaluation",
        blocking,
        {
            "level3_evaluation_ready": False,
            "level3_downstream_ready": False,
            "official_downstream_completed": False,
            "new_level3_main_results_added": False,
        },
    )
    write_report(payload, "step10B_evaluation_report", "Step 10B Evaluation Report")
    print(f"Step 10B Evaluation Report: {payload['status']}")


if __name__ == "__main__":
    main()
