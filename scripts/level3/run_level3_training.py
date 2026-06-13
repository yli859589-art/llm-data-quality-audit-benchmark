from __future__ import annotations

import argparse

from execution_utils import run_blocked_execution_stage, write_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Level 3 training or write honest blocked reports.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def main() -> None:
    _parse_args()
    small = run_blocked_execution_stage(
        "small_training",
        "step10B_small_training_report",
        "Step 10B Small Training Report",
        "level3_small_training_ready",
    )
    medium = {
        **small,
        "stage": "medium_training",
        "level3_small_training_ready": False,
        "level3_medium_training_ready": False,
        "model_scale": "medium",
    }
    write_report(medium, "step10B_medium_training_report", "Step 10B Medium Training Report")
    large_lite = {
        **small,
        "stage": "large_lite_training",
        "level3_small_training_ready": False,
        "level3_large_lite_ready": False,
        "model_scale": "large_lite",
        "exploratory": True,
    }
    write_report(large_lite, "step10B_large_lite_report", "Step 10B Large-Lite Report")
    print("Step 10B training reports: blocked")


if __name__ == "__main__":
    main()

