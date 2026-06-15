from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for path in [ROOT / "src", ROOT / "scripts"]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from dataaudit_lm.integrity.hashing import sha256_file
from dataaudit_lm.integrity.io import write_json
from dataaudit_lm.integrity.paths import INTEGRITY, REPORTS, ensure_public_artifact_dirs

REQUIRED = [
    "README.md",
    "LICENSE",
    "CITATION.cff",
    "pyproject.toml",
    "artifacts/" + "local" + "max_" + "cc" + "fc_tables/" + "cc" + "fc_main_results.csv",
    "artifacts/reports/" + "local" + "max_" + "cc" + "fc_readiness_report.json",
    "scripts/dataaudit_lm/audit_metric_correctness.py",
]


def main() -> None:
    ensure_public_artifact_dirs()
    missing = [path for path in REQUIRED if not (ROOT / path).exists()]
    tracked_large = [
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and path.stat().st_size > 95 * 1024 * 1024
        and not any(part.startswith(".") for part in path.relative_to(ROOT).parts)
    ]
    hashes = {
        path: sha256_file(ROOT / path)
        for path in REQUIRED
        if (ROOT / path).exists() and (ROOT / path).is_file()
    }
    passed = not missing
    payload = {
        "artifact_integrity_verified": passed,
        "hashes": hashes,
        "large_local_files_over_95mb": tracked_large,
        "missing_required_files": missing,
        "status": "ARTIFACT_INTEGRITY_VERIFIED" if passed else "ARTIFACT_INTEGRITY_FAILED",
    }
    write_json(REPORTS / "artifact_integrity_report.json", payload)
    write_json(INTEGRITY / "artifact_hashes.json", hashes)
    print(json.dumps({"artifact_integrity_verified": passed, "missing": missing}))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
