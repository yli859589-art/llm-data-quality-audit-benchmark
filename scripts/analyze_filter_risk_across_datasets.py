from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

from analyze_cross_dataset_audit import analyze


def main() -> None:
    result = analyze()
    print(f"Filter risk analysis refreshed: {result['failure_rows']} failure rows")


if __name__ == "__main__":
    main()
