from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "src"
if str(src) not in sys.path:
    sys.path.insert(0, str(src))

parser = argparse.ArgumentParser()
parser.add_argument("--artifact-dir", default="artifacts/quick_experiment")
args = parser.parse_args()

artifact_dir = root / args.artifact_dir
payload = json.loads((artifact_dir / "results.json").read_text(encoding="utf-8"))
documents = [row["document_index"] for row in payload["quality_scores"]]
if not documents:
    raise SystemExit("No quality-score rows found; run scripts/run_quick_experiment.py first.")

report = payload.get("hdqs_sweep_report")
if report is None:
    raise SystemExit("results.json does not include hdqs_sweep_report; rerun quick experiment.")

(artifact_dir / "hdqs_sweep_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(f"HDQS sweep report refreshed: {artifact_dir / 'hdqs_sweep_report.json'}")
