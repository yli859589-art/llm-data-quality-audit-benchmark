from __future__ import annotations

import argparse

from execution_utils import run_blocked_execution_stage


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Level 3 filters or write an honest blocked report.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def main() -> None:
    _parse_args()
    run_blocked_execution_stage(
        "filter",
        "step10B_filter_report",
        "Step 10B Filter Report",
        "level3_filters_ready",
    )


if __name__ == "__main__":
    main()

