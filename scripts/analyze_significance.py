from __future__ import annotations

import argparse

from experiment_utils import root

from stats.significance import analyze_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="artifacts/runs/run_registry.csv")
    parser.add_argument("--output", default="artifacts/stats")
    args = parser.parse_args()
    result = analyze_registry(root / args.input, root / args.output)
    print(f"Significance summaries: {len(result['summaries'])}")
    print(f"Claim safety: {root / args.output / 'claim_safety_report.md'}")


if __name__ == "__main__":
    main()
