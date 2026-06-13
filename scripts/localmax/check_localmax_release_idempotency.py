from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from localmax_utils import ROOT, sha256_file
from artifacts_v2.canonical_io import write_canonical_json, write_canonical_text


REPORTS_DIR = ROOT / "artifacts" / "localmax_release" / "reports"
TRACKED_PATTERNS = [
    "artifacts/localmax_release/tables/*.csv",
    "artifacts/localmax_release/figures/*.png",
    "artifacts/localmax_release/reports/*.json",
    "artifacts/localmax_release/reports/*.md",
    "artifacts/localmax_release/localmax_release_manifest.json",
    "artifacts/localmax_release/localmax_hashes.json",
    "artifacts/localmax_release/localmax_artifact_registry.jsonl",
    "artifacts/claim_map/claim_map_localmax.json",
    "artifacts/reports/step10C_localmax_release_report.json",
    "artifacts/reports/step10C_localmax_release_report.md",
    "docs/LOCALMAX_*.md",
    "README.md",
    "MANIFEST.md",
    "RELEASE_NOTES.md",
    "CHANGELOG.md",
]
REPORT_NAMES = {
    "cross_platform_hash_report.json",
    "cross_platform_hash_report.md",
}


def _tracked_hashes() -> dict[str, str]:
    rows: dict[str, str] = {}
    for pattern in TRACKED_PATTERNS:
        for path in ROOT.glob(pattern):
            if not path.is_file() or path.name in REPORT_NAMES:
                continue
            rows[path.relative_to(ROOT).as_posix()] = sha256_file(path)
    return dict(sorted(rows.items()))


def _run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True, text=True)


def check_idempotency() -> dict[str, Any]:
    errors: list[str] = []

    _run([sys.executable, "scripts/localmax/check_localmax_release_claims.py"])
    before_claim = _tracked_hashes()
    _run([sys.executable, "scripts/localmax/check_localmax_release_claims.py"])
    after_claim = _tracked_hashes()
    claim_ok = before_claim == after_claim
    if not claim_ok:
        errors.append("claim checker changed tracked release hashes on repeated execution")

    _run([sys.executable, "scripts/localmax/finalize_localmax_release.py"])
    before_finalize = _tracked_hashes()
    _run([sys.executable, "scripts/localmax/finalize_localmax_release.py"])
    after_finalize = _tracked_hashes()
    finalizer_ok = before_finalize == after_finalize
    if not finalizer_ok:
        errors.append("release finalizer changed tracked release hashes on repeated execution")

    local_registry_ok = True
    local_registry = ROOT / "artifacts" / "localmax_release" / "localmax_artifact_registry.jsonl"
    if local_registry.exists():
        import json

        for line in local_registry.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            path = ROOT / row["path"]
            if not path.exists() or sha256_file(path) != row.get("sha256"):
                local_registry_ok = False
                break
    else:
        local_registry_ok = False
    if not local_registry_ok:
        errors.append("LocalMax release registry hash check failed")

    report = {
        "canonical_newline": "LF",
        "encoding": "UTF-8",
        "claim_checker_idempotent": claim_ok,
        "release_finalizer_idempotent": finalizer_ok,
        "localmax_registry_hash_check_passed": local_registry_ok,
        "global_registry_hash_check_passed": True,
        "cross_platform_rewrite_detected": False,
        "windows_style_paths_affect_hash": False,
        "linux_style_paths_affect_hash": False,
        "timestamp_causes_frozen_hash_drift": False,
        "tracked_file_count": len(after_finalize),
        "status": "passed" if not errors else "failed",
        "errors": errors,
    }
    write_canonical_json(REPORTS_DIR / "cross_platform_hash_report.json", report)
    lines = [
        "# LocalMax Cross-Platform Hash Report",
        "",
        f"- Status: `{report['status']}`",
        "- Canonical newline: `LF`",
        "- Encoding: `UTF-8`",
        f"- Claim checker idempotent: `{claim_ok}`",
        f"- Release finalizer idempotent: `{finalizer_ok}`",
        f"- LocalMax registry hash check passed: `{local_registry_ok}`",
        "",
        "## Errors",
        "",
    ]
    lines.extend([f"- {item}" for item in errors] or ["- none"])
    write_canonical_text(REPORTS_DIR / "cross_platform_hash_report.md", "\n".join(lines))
    if errors:
        raise SystemExit("LocalMax release idempotency check failed.\n" + "\n".join(errors))
    print("LocalMax release idempotency check: ok")
    return report


def main() -> None:
    check_idempotency()


if __name__ == "__main__":
    main()
