from __future__ import annotations

import argparse

from execution_utils import run_blocked_execution_stage


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Level 3 mechanism analysis or write an honest blocked report.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def main() -> None:
    _parse_args()
    run_blocked_execution_stage(
        "mechanism",
        "step10B_mechanism_report",
        "Step 10B Mechanism Report",
        "level3_mechanism_ready",
    )


if __name__ == "__main__":
    main()

