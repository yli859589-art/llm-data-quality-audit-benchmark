from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark import BenchmarkConfig, run_benchmark
from course_project_suite.llm_benchmark.char_lm import TrainConfig
from course_project_suite.llm_benchmark.statistics import aggregate_model_runs

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=["quick", "paper-prototype"], default="quick")
parser.add_argument("--seeds", default=None, help="Comma-separated integer seeds.")
parser.add_argument("--output-dir", default=None)
args = parser.parse_args()

if args.seeds:
    seeds = tuple(int(value.strip()) for value in args.seeds.split(",") if value.strip())
elif args.mode == "paper-prototype":
    seeds = (23, 42, 3407)
else:
    seeds = (23,)

steps = 8 if args.mode == "quick" else 12
output_dir = root / (args.output_dir or f"artifacts/multi_seed_{args.mode}")
payload = run_benchmark(
    BenchmarkConfig(
        data_path=str(root / "data" / "tinyshakespeare" / "input.txt"),
        output_dir=str(output_dir),
        mode=f"multi_seed_{args.mode}",
        train_config=TrainConfig(steps=steps, eval_interval=4, eval_batches=2, n_embd=24),
        seeds=seeds,
    )
)
seed_rows, aggregate_rows, tests = aggregate_model_runs(payload["model_runs"])

with (output_dir / "seed_level_results.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0]))
    writer.writeheader()
    writer.writerows(seed_rows)
with (output_dir / "aggregated_results.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(aggregate_rows[0]))
    writer.writeheader()
    writer.writerows(aggregate_rows)
(output_dir / "statistical_tests.json").write_text(json.dumps(tests, indent=2), encoding="utf-8")
print(f"Multi-seed experiment complete: {output_dir}")
print(f"Mode: {args.mode}; seeds: {','.join(str(seed) for seed in seeds)}")
