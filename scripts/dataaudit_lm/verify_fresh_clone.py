from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.io import write_json
from dataaudit_lm.integrity.paths import INTEGRITY, ensure_public_artifact_dirs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--light", action="store_true")
    args = parser.parse_args()
    ensure_public_artifact_dirs()
    commands = [
        [sys.executable, "scripts/dataaudit_lm/audit_metric_correctness.py"],
        [sys.executable, "scripts/dataaudit_lm/verify_artifacts.py"],
    ]
    results = []
    with tempfile.TemporaryDirectory(prefix="dataaudit_lm_verify_") as tmp:
        for command in commands:
            proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            results.append(
                {
                    "command": command,
                    "returncode": proc.returncode,
                    "stdout_tail": proc.stdout[-2000:],
                    "stderr_tail": proc.stderr[-2000:],
                }
            )
        scratch = Path(tmp)
    passed = all(result["returncode"] == 0 for result in results)
    payload = {
        "fresh_clone_light": bool(args.light),
        "fresh_clone_verified": passed,
        "results": results,
        "scratch_removed": not scratch.exists(),
        "status": "FRESH_CLONE_LIGHT_VERIFIED" if passed else "FRESH_CLONE_LIGHT_FAILED",
    }
    write_json(INTEGRITY / "fresh_clone_report.json", payload)
    print(json.dumps({"fresh_clone_verified": passed, "light": bool(args.light)}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
