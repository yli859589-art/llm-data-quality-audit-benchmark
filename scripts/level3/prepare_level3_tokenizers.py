from __future__ import annotations

import argparse

from execution_utils import run_blocked_execution_stage


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Level 3 tokenizers or write an honest blocked report.")
    parser.add_argument("--config", required=True)
    return parser.parse_args()


def main() -> None:
    _parse_args()
    run_blocked_execution_stage(
        "tokenizer",
        "step10B_tokenizer_report",
        "Step 10B Tokenizer Report",
        "level3_tokenizer_ready",
    )


if __name__ == "__main__":
    main()

