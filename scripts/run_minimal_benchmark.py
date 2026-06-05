from __future__ import annotations

from _bootstrap import bootstrap, build_subprocess_env

bootstrap()

import argparse
import subprocess
import sys
from pathlib import Path

from experiment_utils import root
from registry_utils import read_registry_jsonl


DEFAULT_METHODS = ["raw", "dedup_only", "hdqspp_v3"]


def _has_completed(method: str, seed: int) -> bool:
    for row in reversed(read_registry_jsonl()):
        if row.get("dataset_key") != "wikitext2_paper":
            continue
        if row.get("model_size") != "small":
            continue
        if row.get("baseline_name") != method:
            continue
        if str(row.get("seed")) != str(seed):
            continue
        if row.get("run_status") != "completed_training":
            continue
        if int(float(row.get("train_tokens") or 0)) < 1_000_000:
            continue
        if int(float(row.get("evaluated_validation_tokens") or 0)) < 50_000:
            continue
        return True
    return False


def _run(command: list[str], *, dry_run: bool) -> None:
    print("RUN", " ".join(command), flush=True)
    if not dry_run:
        subprocess.run(command, cwd=root, env=build_subprocess_env(), check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    parser.add_argument("--model", default="configs/models/small.yaml")
    parser.add_argument("--methods", nargs="*", default=DEFAULT_METHODS)
    parser.add_argument("--seeds", nargs="*", type=int, default=[1])
    parser.add_argument("--train", action="store_true", help="Actually run missing training rows.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--quick-check",
        action="store_true",
        help="Validate the existing minimal benchmark without writing new training rows.",
    )
    args = parser.parse_args()
    dry_run = args.dry_run or args.quick_check or not args.train

    _run([sys.executable, "scripts/prepare_real_data.py", "--config", "configs/data/wikitext2_paper.yaml"], dry_run=args.dry_run)
    missing = [
        (method, seed)
        for method in args.methods
        for seed in args.seeds
        if not _has_completed(method, seed)
    ]
    if missing and dry_run:
        print("Missing completed-training rows:", ", ".join(f"{m}/seed_{s}" for m, s in missing))
        print("Use --train to generate missing rows. Quick-check does not write main_results.")
    elif missing:
        for method in args.methods:
            method_missing = [seed for row_method, seed in missing if row_method == method]
            if not method_missing:
                continue
            _run(
                [
                    sys.executable,
                    "scripts/run_experiment.py",
                    "--config",
                    args.config,
                    "--model",
                    args.model,
                    "--methods",
                    method,
                    "--seeds",
                    *[str(seed) for seed in method_missing],
                ],
                dry_run=args.dry_run,
            )
    else:
        print("Existing completed-training rows cover the minimal benchmark.")

    for command in [
        [sys.executable, "scripts/analyze_significance.py", "--input", "artifacts/runs/run_registry.csv", "--output", "artifacts/stats"],
        [sys.executable, "scripts/generate_tables.py"],
        [sys.executable, "scripts/generate_figures.py"],
        [sys.executable, "scripts/generate_project_dashboard.py"],
        [sys.executable, "scripts/check_main_results_purity.py"],
        [sys.executable, "scripts/check_experiment_readiness.py"],
    ]:
        _run(command, dry_run=args.dry_run)
    print("Minimal benchmark quick-check complete.")


if __name__ == "__main__":
    main()
