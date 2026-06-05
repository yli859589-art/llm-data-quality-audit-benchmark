from __future__ import annotations

from _bootstrap import bootstrap, build_subprocess_env

bootstrap()

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str]) -> None:
    print("RUN", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=build_subprocess_env(), check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    parser.add_argument("--model", default="configs/models/small.yaml")
    parser.add_argument(
        "--methods",
        nargs="*",
        default=["raw", "random_same_keep_rate", "dedup_only", "length_filter", "hdqspp", "hdqspp_v2", "hdqspp_v3"],
    )
    parser.add_argument("--seeds", nargs="*", type=int, default=[1, 2, 3])
    parser.add_argument("--skip-training", action="store_true")
    args = parser.parse_args()
    if not args.skip_training:
        _run(
            [
                sys.executable,
                "scripts/run_experiment.py",
                "--config",
                args.config,
                "--model",
                args.model,
                "--methods",
                *args.methods,
                "--seeds",
                *[str(seed) for seed in args.seeds],
            ]
        )
    for command in [
        [sys.executable, "scripts/analyze_significance.py", "--input", "artifacts/runs/run_registry.csv", "--output", "artifacts/stats"],
        [sys.executable, "scripts/generate_tables.py"],
        [sys.executable, "scripts/generate_figures.py"],
        [sys.executable, "scripts/generate_project_dashboard.py"],
        [sys.executable, "scripts/check_main_results_purity.py"],
        [sys.executable, "scripts/check_experiment_readiness.py"],
    ]:
        _run(command)
    print("Audit benchmark run complete.")


if __name__ == "__main__":
    main()
