from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

from clean_artifacts import clean_generated_paths
from experiment_utils import root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    protected = [
        "artifacts/runs/run_registry.jsonl",
        "artifacts/runs/run_registry.csv",
        "artifacts/tables/main_results.csv",
        "artifacts/stats/main_results.csv",
        "artifacts/diagnostics",
        "artifacts/stats",
        "artifacts/figures",
    ]
    removed = clean_generated_paths(root, dry_run=args.dry_run)
    log = {
        "timestamp_utc": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "dry_run": args.dry_run,
        "removed_count": len(removed),
        "removed_paths": removed,
        "protected_artifacts": protected,
        "policy": "cache-only cleanup; registry, main results, diagnostics, stats, and audit artifacts are preserved",
    }
    log_path = root / "artifacts" / "cleanup_log.json"
    log_path.write_text(json.dumps(log, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Cleanup log: {log_path.relative_to(root).as_posix()}")
    print(f"Removed paths: {len(removed)}")


if __name__ == "__main__":
    main()
