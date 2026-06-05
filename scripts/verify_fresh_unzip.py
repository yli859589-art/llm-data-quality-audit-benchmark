from __future__ import annotations

from _bootstrap import bootstrap

bootstrap()

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from experiment_utils import root
from subprocess_utils import command_text, run_command


REQUIRED_FILES = [
    "README.md",
    "Makefile",
    "PROJECT_SUMMARY.md",
    "PROJECT_ONE_PAGE.md",
    "TECHNICAL_OVERVIEW.md",
    "DEMO_GUIDE.md",
    "RESUME_BULLETS.md",
    "scripts/run_all_checks.py",
    "scripts/run_release_checks.py",
    "scripts/check_experiment_readiness.py",
    "scripts/check_claim_hygiene.py",
    "scripts/verify_fresh_unzip.py",
    "scripts/generate_final_release_report.py",
    "artifacts/tables/main_results.csv",
    "artifacts/release/fresh_unzip_report.json",
    "artifacts/release/fresh_unzip_report.md",
    "artifacts/release/final_release_report.json",
    "artifacts/release/final_release_report.md",
    "docs/QUICKSTART.md",
    "docs/README.md",
    "docs/REPORTING_CONTRACT.md",
    "docs/FIGURE_INDEX.md",
    "docs/PROJECT_PRESENTATION_NOTES.md",
    "docs/future_publication_notes/README.md",
]
REQUIRED_ONE_OF = [["requirements.txt", "pyproject.toml"]]
CACHE_PATTERN = re.compile(
    r"__pycache__|\.pyc$|\.pytest_cache|\.ruff_cache|\.mypy_cache|\.coverage|\.ipynb_checkpoints"
)
ABSOLUTE_PATH_PATTERN = re.compile(
    r"(?:(?<![A-Za-z])[A-Za-z]:(?:\\+|/(?!/))|/(?:home|Users|mnt/data|tmp)(?:/|$))"
)
TEXT_SUFFIXES = {".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".py", ".toml", ".cff"}


def _sanitize_report_text(text: str) -> str:
    text = text.replace(str(Path(sys.executable)), "python")
    text = re.sub(r"[A-Za-z]:[\\/]+Users[\\/]+[^'\"\r\n ]+", "<local_user_path>", text)
    text = re.sub(r"[A-Za-z]:[\\/]+[^'\"\r\n ]+", "<local_absolute_path>", text)
    text = re.sub(r"/(?:home|Users|mnt/data|tmp)/[^'\"\r\n ]+", "<local_absolute_path>", text)
    return text


def _build_env(package_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    paths = [str(package_root / "src"), str(package_root / "scripts")]
    existing = env.get("PYTHONPATH")
    if existing:
        paths.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(paths)
    return env


def _package_root(extract_dir: Path) -> Path:
    if (extract_dir / "README.md").exists():
        return extract_dir
    children = [path for path in extract_dir.iterdir() if path.is_dir()]
    if len(children) == 1 and (children[0] / "README.md").exists():
        return children[0]
    raise RuntimeError("Fresh unzip does not contain a recognizable package root.")


def _zip_sha256(zip_path: Path) -> str:
    return hashlib.sha256(zip_path.read_bytes()).hexdigest()


def _check_zip_contents(zip_path: Path) -> tuple[list[str], list[str], list[str]]:
    cache_hits: list[str] = []
    nested_zip_hits: list[str] = []
    absolute_hits: list[str] = []
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            normalized = name.replace("\\", "/")
            if CACHE_PATTERN.search(normalized):
                cache_hits.append(normalized)
            if normalized.lower().endswith(".zip"):
                nested_zip_hits.append(normalized)
            if Path(normalized).suffix.lower() not in TEXT_SUFFIXES and Path(normalized).name not in {".gitignore"}:
                continue
            try:
                text = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if ABSOLUTE_PATH_PATTERN.search(text):
                absolute_hits.append(normalized)
    return cache_hits, nested_zip_hits, absolute_hits


def _check_required_files(package_root: Path) -> list[str]:
    missing = [path for path in REQUIRED_FILES if not (package_root / path).exists()]
    for alternatives in REQUIRED_ONE_OF:
        if not any((package_root / item).exists() for item in alternatives):
            missing.append(" one of " + ", ".join(alternatives))
    return missing


def _run_step(
    *,
    name: str,
    command: list[str],
    cwd: Path,
    env: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    result = {
        "name": name,
        "command": _sanitize_report_text(command_text(command)),
        "status": "passed",
        "returncode": 0,
    }
    try:
        run_command(command, cwd=cwd, env=env, timeout=timeout)
    except SystemExit as exc:
        code = int(exc.code) if isinstance(exc.code, int) else 1
        result["status"] = "failed_due_to_timeout" if code == 124 else "failed"
        result["returncode"] = code
    except FileNotFoundError as exc:
        result["status"] = "not_run_due_to_environment"
        result["returncode"] = 127
        result["error"] = _sanitize_report_text(f"{type(exc).__name__}: {exc}")
    return result


def _write_reports(report: dict[str, Any]) -> None:
    output_dir = root / "artifacts" / "release"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "fresh_unzip_report.json"
    md_path = output_dir / "fresh_unzip_report.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Fresh-Unzip Verification Report",
        "",
        f"- Status: `{report['status']}`",
        f"- Zip file name: `{report['zip_file_name']}`",
        f"- Zip path: `{report.get('zip_path', '')}`",
        f"- Zip SHA-256: `{report['zip_sha256']}`",
        f"- lightweight_check_status: `{report['lightweight_check_status']}`",
        f"- heavy_check_status: `{report['heavy_check_status']}`",
        f"- heavy_check_reason: {report.get('heavy_check_reason', '')}",
        "",
        "## Structure Checks",
        "",
        f"- Missing required files: `{len(report['missing_required_files'])}`",
        f"- Cache files in zip: `{len(report['zip_cache_hits'])}`",
        f"- Nested zip files: `{len(report['nested_zip_hits'])}`",
        f"- Local absolute path hits: `{len(report['absolute_path_hits'])}`",
        f"- cache_scan_status: `{report.get('cache_scan_status', '')}`",
        f"- nested_zip_scan_status: `{report.get('nested_zip_scan_status', '')}`",
        f"- local_absolute_path_scan_status: `{report.get('local_absolute_path_scan_status', '')}`",
        "",
        "## Checked Files",
        "",
    ]
    lines.extend(f"- `{path}`" for path in report.get("checked_files", []))
    lines.extend(
        [
        "",
        "## Lightweight Steps",
        "",
        "| Step | Status | Return code |",
        "|---|---|---:|",
        ]
    )
    for step in report["lightweight_steps"]:
        lines.append(f"| `{step['name']}` | `{step['status']}` | {step['returncode']} |")
    lines.extend(["", "## Heavy Steps", "", "| Step | Status | Return code |", "|---|---|---:|"])
    for step in report["heavy_steps"]:
        lines.append(f"| `{step['name']}` | `{step['status']}` | {step['returncode']} |")
    if not report["heavy_steps"]:
        lines.append(f"| `run_all_checks` | `{report['heavy_check_status']}` |  |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def verify(zip_path: Path, timeout: int, skip_heavy: bool = False) -> dict[str, Any]:
    zip_path = zip_path.resolve()
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path.name}")

    cache_hits, nested_zip_hits, absolute_hits = _check_zip_contents(zip_path)
    report: dict[str, Any] = {
        "status": "passed",
        "zip_file_name": zip_path.name,
        "zip_path": _sanitize_report_text(str(zip_path)),
        "zip_sha256": _zip_sha256(zip_path),
        "checked_files": REQUIRED_FILES,
        "required_one_of": REQUIRED_ONE_OF,
        "missing_required_files": [],
        "zip_cache_hits": cache_hits,
        "nested_zip_hits": nested_zip_hits,
        "absolute_path_hits": absolute_hits,
        "cache_scan_status": "passed" if not cache_hits else "failed",
        "nested_zip_scan_status": "passed" if not nested_zip_hits else "failed",
        "local_absolute_path_scan_status": "passed" if not absolute_hits else "failed",
        "lightweight_check_status": "not_run",
        "heavy_check_status": "skipped_by_request" if skip_heavy else "not_run",
        "heavy_check_reason": "skip-heavy flag was provided" if skip_heavy else "",
        "lightweight_steps": [],
        "heavy_steps": [],
    }

    with tempfile.TemporaryDirectory(prefix="fresh_unzip_") as temp:
        extract_dir = Path(temp)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(extract_dir)
        package_root = _package_root(extract_dir)
        missing = _check_required_files(package_root)
        report["missing_required_files"] = missing
        env = _build_env(package_root)
        lightweight_commands = [
            ("check_experiment_readiness", [sys.executable, "scripts/check_experiment_readiness.py"]),
            ("check_claim_hygiene", [sys.executable, "scripts/check_claim_hygiene.py"]),
            (
                "run_release_checks_skip_core_zip",
                [
                    sys.executable,
                    "scripts/run_release_checks.py",
                    "--skip-core-checks",
                    "--zip",
                    str(zip_path),
                    "--timeout",
                    str(timeout),
                ],
            ),
        ]
        lightweight_steps = [
            _run_step(name=name, command=command, cwd=package_root, env=env, timeout=timeout)
            for name, command in lightweight_commands
        ]
        report["lightweight_steps"] = lightweight_steps
        report["lightweight_check_status"] = (
            "passed" if all(step["status"] == "passed" for step in lightweight_steps) else "failed"
        )
        if not skip_heavy:
            heavy_step = _run_step(
                name="run_all_checks",
                command=[sys.executable, "scripts/run_all_checks.py", "--timeout", str(timeout)],
                cwd=package_root,
                env=env,
                timeout=timeout * 4,
            )
            report["heavy_steps"] = [heavy_step]
            report["heavy_check_status"] = heavy_step["status"]
            report["heavy_check_reason"] = (
                "run_all_checks completed"
                if heavy_step["status"] == "passed"
                else f"run_all_checks ended with status {heavy_step['status']}"
            )

    structure_ok = not cache_hits and not nested_zip_hits and not absolute_hits and not report["missing_required_files"]
    lightweight_ok = report["lightweight_check_status"] == "passed"
    heavy_ok = skip_heavy or report["heavy_check_status"] == "passed"
    report["status"] = "passed" if structure_ok and lightweight_ok and heavy_ok else "failed"
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True, help="Release zip to extract and verify.")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--skip-heavy", action="store_true")
    args = parser.parse_args()
    try:
        report = verify(Path(args.zip), timeout=args.timeout, skip_heavy=args.skip_heavy)
    except Exception as exc:
        report = {
            "status": "failed",
            "zip_file_name": Path(args.zip).name,
            "zip_path": _sanitize_report_text(str(Path(args.zip))),
            "zip_sha256": "",
            "checked_files": REQUIRED_FILES,
            "required_one_of": REQUIRED_ONE_OF,
            "missing_required_files": [],
            "zip_cache_hits": [],
            "nested_zip_hits": [],
            "absolute_path_hits": [],
            "cache_scan_status": "not_run_due_to_environment",
            "nested_zip_scan_status": "not_run_due_to_environment",
            "local_absolute_path_scan_status": "not_run_due_to_environment",
            "lightweight_check_status": "failed",
            "heavy_check_status": "not_run_due_to_environment",
            "heavy_check_reason": "fresh-unzip setup failed before heavy checks",
            "lightweight_steps": [],
            "heavy_steps": [],
            "error": _sanitize_report_text(f"{type(exc).__name__}: {exc}"),
        }
    _write_reports(report)
    print(f"Fresh unzip verification: {report['status']}")
    print("Report: artifacts/release/fresh_unzip_report.json")
    if report["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
