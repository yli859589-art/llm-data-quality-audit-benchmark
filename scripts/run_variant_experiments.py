from __future__ import annotations

from _bootstrap import bootstrap, build_subprocess_env

bootstrap()

import argparse
import subprocess
import sys

from experiment_utils import root
from registry_utils import read_registry_jsonl


REQUIRED_METHODS = [
    "raw",
    "random_same_keep_rate",
    "dedup_only",
    "hdqspp",
    "hdqspp_v2",
    "hdqspp_v2_no_token_frequency",
    "hdqspp_v3",
]


def _has_completed(method: str, seed: int) -> bool:
    for row in reversed(read_registry_jsonl()):
        if row.get("dataset_key") != "wikitext2_paper":
            continue
        if row.get("dataset_status") not in {"real_nonfallback", "real_local_nonfallback"}:
            continue
        if row.get("dataset_scope") != "official_split":
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/dev.yaml")
    parser.add_argument("--model", default="configs/models/small.yaml")
    parser.add_argument("--seeds", nargs="*", type=int, default=[1, 2, 3])
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    commands: list[list[str]] = []
    for method in REQUIRED_METHODS:
        missing = [seed for seed in args.seeds if args.force or not _has_completed(method, seed)]
        if not missing:
            print(f"{method}: existing completed_training rows cover seeds {args.seeds}")
            continue
        command = [
            sys.executable,
            "scripts/run_experiment.py",
            "--config",
            args.config,
            "--model",
            args.model,
            "--methods",
            method,
            "--seeds",
            *[str(seed) for seed in missing],
        ]
        commands.append(command)

    if not commands:
        print("Variant experiment matrix already complete.")
        return

    for command in commands:
        print("Running:", " ".join(command))
        subprocess.run(command, cwd=root, env=build_subprocess_env(), check=True)


if __name__ == "__main__":
    main()
