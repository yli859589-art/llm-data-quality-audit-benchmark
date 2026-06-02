from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
env = os.environ.copy()
env["PYTHONPATH"] = str(root / "src") + os.pathsep + env.get("PYTHONPATH", "")

try:
    import coverage  # noqa: F401
except ImportError as exc:
    raise SystemExit(
        "Install development dependencies first: python -m pip install -r requirements-dev.txt"
    ) from exc


def run(*args: str, capture: bool = False) -> str:
    completed = subprocess.run(
        args, cwd=root, env=env, check=True, capture_output=capture, text=True
    )
    return completed.stdout


run(sys.executable, "-m", "coverage", "erase")
run(
    sys.executable,
    "-m",
    "coverage",
    "run",
    "--source=course_project_suite",
    "-m",
    "unittest",
    "discover",
    "-s",
    "tests",
    "-v",
)
run(
    sys.executable,
    "-m",
    "coverage",
    "run",
    "--append",
    "--source=course_project_suite",
    "scripts/run_quick_experiment.py",
)
report = run(sys.executable, "-m", "coverage", "report", "-m", capture=True)
(root / "docs" / "COVERAGE_REPORT.txt").write_text(report, encoding="utf-8")
run(sys.executable, "-m", "coverage", "xml", "-o", "coverage.xml")
print(report)
print("Coverage report written to docs/COVERAGE_REPORT.txt and coverage.xml")
