from __future__ import annotations

import argparse
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark.reporting import regenerate_figures_from_results

parser = argparse.ArgumentParser()
parser.add_argument("--artifact-dir", default="artifacts/quick_experiment")
args = parser.parse_args()
artifact_dir = root / args.artifact_dir
regenerate_figures_from_results(artifact_dir / "results.json")
print(f"Figures regenerated in {artifact_dir}")
