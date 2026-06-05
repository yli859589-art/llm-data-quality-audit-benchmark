from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import sys
import zipfile
from pathlib import Path

from _bootstrap import bootstrap, build_subprocess_env
from subprocess_utils import run_command


ROOT = Path(__file__).resolve().parents[1]
bootstrap()
REQUIRED_DOCS = [
    "README.md",
    "MANIFEST.md",
    "RELEASE_NOTES.md",
    "PROJECT_SUMMARY.md",
    "PROJECT_ONE_PAGE.md",
    "TECHNICAL_OVERVIEW.md",
    "DEMO_GUIDE.md",
    "RESUME_BULLETS.md",
    "docs/README.md",
    "docs/QUICKSTART.md",
    "docs/REPRODUCIBILITY.md",
    "docs/BENCHMARK_PROTOCOL.md",
    "docs/ARTIFACT_INDEX.md",
    "docs/LIMITATIONS.md",
    "docs/FAILURE_CASES.md",
    "docs/PROJECT_STATUS.md",
    "docs/PROJECT_EVIDENCE_MAP.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/FRESH_CLONE_TEST.md",
    "docs/CROSS_DATASET_AUDIT.md",
    "docs/REPORTING_CONTRACT.md",
    "docs/PROJECT_PRESENTATION_NOTES.md",
    "docs/FIGURE_INDEX.md",
    "docs/future_publication_notes/README.md",
    "artifacts/release/fresh_unzip_report.json",
    "artifacts/release/fresh_unzip_report.md",
    "artifacts/release/final_release_report.json",
    "artifacts/release/final_release_report.md",
]
REQUIRED_SCRIPTS = [
    "scripts/_bootstrap.py",
    "scripts/subprocess_utils.py",
    "scripts/check_claim_hygiene.py",
    "scripts/verify_fresh_unzip.py",
    "scripts/generate_final_release_report.py",
    "scripts/prepare_streaming_data.py",
    "scripts/run_all_checks.py",
    "scripts/run_minimal_benchmark.py",
    "scripts/run_audit_benchmark.py",
    "scripts/run_release_checks.py",
    "scripts/clean_project_artifacts.py",
    "scripts/generate_project_dashboard.py",
    "scripts/generate_cross_dataset_tables.py",
    "scripts/analyze_cross_dataset_audit.py",
    "scripts/analyze_dataset_shift.py",
    "scripts/analyze_filter_risk_across_datasets.py",
]


def _run(command: list[str], timeout: int) -> None:
    run_command(command, cwd=ROOT, env=build_subprocess_env(), timeout=timeout)


def _subprocess_env_for(package_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    paths = [str(package_root / "src"), str(package_root / "scripts")]
    existing = env.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def _assert_exists(paths: list[str]) -> None:
    missing = [path for path in paths if not (ROOT / path).exists()]
    if missing:
        raise SystemExit("Missing release files: " + ", ".join(missing))


def _check_method_status() -> None:
    readiness = json.loads((ROOT / "artifacts/experiment_readiness_report.json").read_text(encoding="utf-8"))
    if readiness.get("method_status") != "honest_audit_framework":
        raise SystemExit("experiment_readiness_report method_status is not honest_audit_framework")
    if readiness.get("ccf_c_ready") is not False:
        raise SystemExit("ccf_c_ready must remain false")
    status_text = (ROOT / "artifacts/stats/method_status_report.md").read_text(encoding="utf-8")
    if "- Method status: `honest_audit_framework`" not in status_text:
        raise SystemExit("method_status_report does not use honest_audit_framework as the primary status")
    if "secondary" not in status_text.casefold():
        raise SystemExit("method_status_report must keep the v3-over-v2 finding as secondary")


def _check_readme_commands() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    commands = re.findall(r"^python\s+scripts/[^\n]+", readme, flags=re.MULTILINE)
    for command in commands:
        script = Path(command.split()[1])
        if not (ROOT / script).exists():
            raise SystemExit(f"README command references missing script: {script.as_posix()}")


def _check_zip(path: Path) -> None:
    if not path.exists():
        raise SystemExit(f"Zip file not found: {path}")
    forbidden = re.compile(r"__pycache__|\.pyc$|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.coverage")
    absolute = re.compile(
        r"(?:(?<![A-Za-z])[A-Za-z]:(?:\\+|/(?!/))|/"
        + "Users"
        + r"/|/"
        + "home"
        + r"/[^/]+/|/"
        + "mnt"
        + "/"
        + "data"
        + "/|/"
        + "tmp"
        + "/)"
    )
    with zipfile.ZipFile(path) as archive:
        names = [name.replace("\\", "/") for name in archive.namelist()]
        bad = [name for name in names if forbidden.search(name)]
        if bad:
            raise SystemExit("Zip contains cache files: " + ", ".join(bad[:10]))
        nested_zip = [name for name in names if name.lower().endswith(".zip")]
        if nested_zip:
            raise SystemExit("Zip contains nested zip files: " + ", ".join(nested_zip[:10]))
        for name in names:
            if not name.lower().endswith((".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".py", ".toml", ".cff")):
                continue
            try:
                text = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if absolute.search(text):
                raise SystemExit(f"Zip text file contains absolute local path: {name}")
        required = {
            "README.md",
            "Makefile",
            "PROJECT_SUMMARY.md",
            "PROJECT_ONE_PAGE.md",
            "TECHNICAL_OVERVIEW.md",
            "DEMO_GUIDE.md",
            "RESUME_BULLETS.md",
            "docs/README.md",
            "docs/REPORTING_CONTRACT.md",
            "docs/FRESH_CLONE_TEST.md",
            "docs/FIGURE_INDEX.md",
            "docs/PROJECT_PRESENTATION_NOTES.md",
            "docs/future_publication_notes/README.md",
            "scripts/subprocess_utils.py",
            "scripts/check_claim_hygiene.py",
            "scripts/verify_fresh_unzip.py",
            "scripts/generate_final_release_report.py",
            "scripts/prepare_streaming_data.py",
            "scripts/run_all_checks.py",
            "scripts/run_release_checks.py",
            "artifacts/tables/main_results.csv",
            "artifacts/cross_dataset/cross_dataset_results.csv",
            "artifacts/cross_dataset/dataset_status_matrix.csv",
            "artifacts/release/claim_hygiene_report.json",
            "artifacts/release/claim_hygiene_report.md",
            "artifacts/release/fresh_unzip_report.json",
            "artifacts/release/fresh_unzip_report.md",
            "artifacts/release/final_release_report.json",
            "artifacts/release/final_release_report.md",
            "docs/QUICKSTART.md",
            "docs/REPRODUCIBILITY.md",
            "docs/BENCHMARK_PROTOCOL.md",
            "docs/ARTIFACT_INDEX.md",
            "docs/CROSS_DATASET_AUDIT.md",
        }
        if not required.issubset(set(names)):
            missing = sorted(required.difference(names))
            raise SystemExit("Zip is missing required root entries: " + ", ".join(missing))


def _package_root(extract_dir: Path) -> Path:
    if (extract_dir / "README.md").exists():
        return extract_dir
    children = [path for path in extract_dir.iterdir() if path.is_dir()]
    if len(children) == 1 and (children[0] / "README.md").exists():
        return children[0]
    raise SystemExit("Fresh unzip does not contain a recognizable package root.")


def _check_fresh_unzip(path: Path, timeout: int) -> None:
    with tempfile.TemporaryDirectory(prefix="stage3c_release_") as temp:
        extract_dir = Path(temp)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(extract_dir)
        package_root = _package_root(extract_dir)
        missing = [entry for entry in REQUIRED_DOCS + REQUIRED_SCRIPTS if not (package_root / entry).exists()]
        if missing:
            raise SystemExit("Fresh unzip missing required files: " + ", ".join(missing))
        run_command(
            [sys.executable, "scripts/check_claim_hygiene.py"],
            cwd=package_root,
            env=_subprocess_env_for(package_root),
            timeout=timeout,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", default="")
    parser.add_argument(
        "--fresh-unzip",
        nargs="?",
        const="__use_zip_argument__",
        default="",
        help="Optionally run fresh-unzip verification. Pass a zip path here or combine with --zip.",
    )
    parser.add_argument("--skip-core-checks", action="store_true")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds for each child command.")
    args = parser.parse_args()
    _assert_exists(REQUIRED_DOCS + REQUIRED_SCRIPTS)
    if not args.skip_core_checks:
        _run([sys.executable, "scripts/run_all_checks.py", "--timeout", str(args.timeout)], timeout=args.timeout * 15)
    _check_readme_commands()
    _check_method_status()
    _run([sys.executable, "scripts/generate_cross_dataset_tables.py"], timeout=args.timeout)
    _run([sys.executable, "scripts/analyze_cross_dataset_audit.py"], timeout=args.timeout)
    _run([sys.executable, "scripts/generate_tables.py"], timeout=args.timeout)
    _run([sys.executable, "scripts/generate_figures.py"], timeout=args.timeout)
    _run([sys.executable, "scripts/generate_project_dashboard.py"], timeout=args.timeout)
    _run([sys.executable, "scripts/check_main_results_purity.py"], timeout=args.timeout)
    _run([sys.executable, "scripts/check_experiment_readiness.py"], timeout=args.timeout)
    _run([sys.executable, "scripts/check_claim_hygiene.py"], timeout=args.timeout)
    fresh_unzip_requested = bool(args.fresh_unzip)
    fresh_zip_arg = "" if args.fresh_unzip == "__use_zip_argument__" else args.fresh_unzip
    zip_argument = fresh_zip_arg or args.zip
    if args.zip or fresh_unzip_requested:
        if not zip_argument:
            raise SystemExit("--fresh-unzip requires a zip path or --zip <path>")
        zip_path = Path(zip_argument)
        _check_zip(zip_path)
        if fresh_unzip_requested:
            _run(
                [
                    sys.executable,
                    "scripts/verify_fresh_unzip.py",
                    "--zip",
                    str(zip_path),
                    "--timeout",
                    str(args.timeout),
                ],
                timeout=args.timeout * 6,
            )
    print("Release checks passed.")


if __name__ == "__main__":
    main()
