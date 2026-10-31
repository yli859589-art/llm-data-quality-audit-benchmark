"""Detached local worker invoked by the web app and CLI."""

from __future__ import annotations

import argparse

from .service import QualitySystemService


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--task-id", required=True)
    args = parser.parse_args()
    QualitySystemService(args.root).execute_task(args.task_id)


if __name__ == "__main__":
    main()
