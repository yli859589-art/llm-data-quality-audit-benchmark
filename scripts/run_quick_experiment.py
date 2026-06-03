from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark import BenchmarkConfig, run_benchmark

payload = run_benchmark(
    BenchmarkConfig(
        data_path=str(root / "data" / "tinyshakespeare" / "input.txt"),
        output_dir=str(root / "artifacts" / "quick_experiment"),
    )
)
print("Quick experiment complete")
print(f"Mode: {payload['mode']}")
print(f"Report: {root / 'artifacts' / 'quick_experiment' / 'REPORT.md'}")
