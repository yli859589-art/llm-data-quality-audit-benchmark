from __future__ import annotations

import csv
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
artifact_dir = root / "artifacts" / "quick_experiment"
payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))

src = root / "src"
import sys

if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.llm_benchmark.statistics import aggregate_model_runs

seed_rows, aggregate_rows, tests = aggregate_model_runs(payload["model_runs"])
with (artifact_dir / "seed_level_results.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(seed_rows[0]))
    writer.writeheader()
    writer.writerows(seed_rows)
with (artifact_dir / "aggregated_results.csv").open("w", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=list(aggregate_rows[0]))
    writer.writeheader()
    writer.writerows(aggregate_rows)
(artifact_dir / "statistical_tests.json").write_text(json.dumps(tests, indent=2), encoding="utf-8")
print(f"Statistical analysis refreshed in {artifact_dir}")
