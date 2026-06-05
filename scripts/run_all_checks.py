from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _bootstrap import bootstrap, build_subprocess_env
from subprocess_utils import run_command


ROOT = Path(__file__).resolve().parents[1]

bootstrap()


def _run(command: list[str], timeout: int) -> None:
    run_command(command, cwd=ROOT, env=build_subprocess_env(), timeout=timeout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--timeout", type=int, default=180, help="Timeout in seconds for each child command.")
    args = parser.parse_args()
    commands = [
        [sys.executable, "scripts/check_repo.py", "--clean"],
    ]
    if not args.skip_tests:
        commands.append([sys.executable, "-m", "pytest", "-q"])
    commands.extend(
        [
            [sys.executable, "scripts/capture_environment.py"],
            [sys.executable, "scripts/check_registry_schema.py"],
            [sys.executable, "scripts/check_artifact_lineage.py"],
            [sys.executable, "scripts/check_main_results_purity.py"],
            [sys.executable, "scripts/check_training_budget_thresholds.py"],
            [sys.executable, "scripts/check_config_not_downgraded.py"],
            [sys.executable, "scripts/check_split_integrity.py"],
            [sys.executable, "scripts/check_no_test_leakage.py"],
            [sys.executable, "scripts/check_no_fallback_in_experiments.py"],
            [sys.executable, "scripts/check_claims_supported.py"],
            [sys.executable, "scripts/check_experiment_readiness.py"],
            [sys.executable, "scripts/check_claim_hygiene.py"],
        ]
    )
    for command in commands:
        _run(command, timeout=args.timeout)
    print("All checks passed.")


if __name__ == "__main__":
    main()
