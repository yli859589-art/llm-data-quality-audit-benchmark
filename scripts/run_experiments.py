from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

from course_project_suite.common import save_json
from course_project_suite.run_all import run_all

results = run_all()
payload = {
    "ok": all(result.ok for result in results),
    "evaluation_protocol": {
        "runtime": "CPU-friendly deterministic local checks",
        "classical_ml": "fixed-seed held-out validation splits and synthetic anomaly probes",
        "recommender": "fixed-seed held-out synthetic rating entries",
        "deep_learning_and_llm": "toy numerical, interface, and forward-pass checks",
    },
    "project_families": len(results),
    "results": [result.to_dict() for result in results],
}
output = root / "docs" / "LATEST_SELF_CHECK_RESULTS.json"
save_json(output, payload)
print(f"Wrote {output.relative_to(root)}")
raise SystemExit(0 if payload["ok"] else 1)
