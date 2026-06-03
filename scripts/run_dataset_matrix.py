from __future__ import annotations

import argparse
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark.dataset_matrix import (
    dataset_keys_for_mode,
    run_dataset_matrix,
)

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["quick", "paper-prototype", "full"], default="quick")
parser.add_argument("--datasets", nargs="*", default=None)
parser.add_argument("--allow-network", action="store_true")
parser.add_argument("--dry-run", action="store_true")
parser.add_argument("--output-dir", default="artifacts/dataset_matrix")
args = parser.parse_args()

dataset_keys = tuple(args.datasets) if args.datasets else dataset_keys_for_mode(args.mode)
rows = run_dataset_matrix(
    root=root,
    output_dir=root / args.output_dir,
    dataset_keys=dataset_keys,
    mode=args.mode,
    allow_network=args.allow_network,
    dry_run=args.dry_run,
)
print(f"Dataset matrix complete: {root / args.output_dir}")
for row in rows:
    print(f"{row.dataset_key}: {row.status}, fallback={row.used_fallback}, output={row.output_dir}")
