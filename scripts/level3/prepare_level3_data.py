from __future__ import annotations

import argparse

from execution_utils import run_blocked_execution_stage


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Level 3 data or write an honest blocked report.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def main() -> None:
    _parse_args()
    run_blocked_execution_stage(
        "data",
        "step10B_data_report",
        "Step 10B Data Report",
        "level3_data_ready",
    )


if __name__ == "__main__":
    main()

